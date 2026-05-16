package logic

import (
	"context"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io"
	"time"

	"app/common/utils"
	"app/internal/client/springClient"
	"app/internal/svc"
	"app/model/search"

	"github.com/olivere/elastic/v7"
)

const (
	esArticlesIndexName = "articles"
	esSyncBatchSize     = 500
	esDateTimeLayout    = "2006-01-02 15:04:05"
)

type esSyncStats struct {
	Added   int
	Updated int
	Deleted int
}

// SyncArticlesToES 增量同步文章到 ElasticSearch
func SyncArticlesToES(ctx context.Context, svcCtx *svc.ServiceContext) error {

	if svcCtx.ESClient == nil {
		if svcCtx.Logger != nil {
			svcCtx.Logger.Error(utils.ES_CLIENT_NOT_INITIALIZED_MESSAGE)
		}
		return fmt.Errorf("%s", utils.ES_CLIENT_NOT_INITIALIZED_MESSAGE)
	}

	exists, err := svcCtx.ESClient.IndexExists(esArticlesIndexName).Do(ctx)
	if err != nil {
		return logAndWrapError(svcCtx, utils.INDEX_CHECK_ERROR_MESSAGE, err)
	}
	if !exists {
		mapping := utils.ES_INDEX_MAPPING
		_, err := svcCtx.ESClient.CreateIndex(esArticlesIndexName).BodyString(mapping).Do(ctx)
		if err != nil {
			return logAndWrapError(svcCtx, utils.INDEX_CREATION_ERROR_MESSAGE, err)
		}
	}

	// 第一步：先把 ES 中当前已有的文章全部扫出来，构造成 id -> hash 的映射
	existingDocs, err := loadExistingESArticles(ctx, svcCtx)
	if err != nil {
		return err
	}

	stats := esSyncStats{}
	batchIdx := 0
	cursor := int64(0)

	for {
		page, err := svcCtx.SpringClient.GetArticleSearchDocs(ctx, cursor, esSyncBatchSize)
		if err != nil {
			return logAndWrapError(svcCtx, utils.ES_BULK_SYNC_ERROR_MESSAGE, err)
		}
		if page == nil || len(page.List) == 0 {
			break
		}
		batchIdx++
		docs := buildArticleESBatch(page.List)

		bulkRequest := svcCtx.ESClient.Bulk()
		batchAdded := 0
		batchUpdated := 0
		for _, doc := range docs {
			// 使用 ES 文档的完整内容计算 hash
			docHash, err := hashArticleES(doc)
			if err != nil {
				return logAndWrapError(svcCtx, utils.ES_BULK_SYNC_ERROR_MESSAGE, err)
			}

			existingHash, ok := existingDocs[doc.ID]
			if !ok {
				// DB 中有、ES 中没有，就新增文档
				bulkRequest = bulkRequest.Add(
					elastic.NewBulkIndexRequest().
						Index(esArticlesIndexName).
						Id(fmt.Sprintf("%d", doc.ID)).
						Doc(doc),
				)
				batchAdded++
			} else if existingHash != docHash {
				// DB 和 ES 都有，但内容 hash 不一致，就更新文档
				bulkRequest = bulkRequest.Add(
					elastic.NewBulkIndexRequest().
						Index(esArticlesIndexName).
						Id(fmt.Sprintf("%d", doc.ID)).
						Doc(doc),
				)
				batchUpdated++
			}

			// 无论是新增、更新还是无变化，只要这篇文章仍存在于 DB 中
			delete(existingDocs, doc.ID)
		}

		// 当前批次只有在确实存在新增/更新操作时才提交到 ES
		if bulkRequest.NumberOfActions() > 0 {
			if err := executeESBulk(ctx, svcCtx, bulkRequest); err != nil {
				return err
			}
		}

		stats.Added += batchAdded
		stats.Updated += batchUpdated

		if svcCtx.Logger != nil {
			svcCtx.Logger.Info(fmt.Sprintf(utils.ES_SYNC_BATCH_COMPLETED_MESSAGE, batchIdx, batchAdded, batchUpdated))
		}

		cursor = page.NextCursor
		if !page.HasMore {
			break
		}
		time.Sleep(200 * time.Millisecond)
	}

	// 第三步：如果遍历完 DB 后，existingDocs 里还有剩余 id，说明这些文档只存在于 ES，当前数据库里已经没有对应的“已发布文章”了
	if len(existingDocs) > 0 {
		deleted, err := deleteStaleESArticles(ctx, svcCtx, existingDocs)
		if err != nil {
			return err
		}
		stats.Deleted = deleted
	}

	if svcCtx.Logger != nil {
		svcCtx.Logger.Info(fmt.Sprintf(utils.ES_INCREMENTAL_SYNC_COMPLETED_MESSAGE, stats.Added, stats.Updated, stats.Deleted))
	}

	if stats.Added == 0 && stats.Updated == 0 && stats.Deleted == 0 && svcCtx.Logger != nil {
		svcCtx.Logger.Info(utils.NO_PUBLISHED_ARTICLES_TO_SYNC_MESSAGE)
	}

	return nil
}

func buildArticleESBatch(
	articleBatch []springClient.ArticleSearchDoc,
) []search.ArticleES {
	docs := make([]search.ArticleES, 0, len(articleBatch))
	for _, article := range articleBatch {
		docs = append(docs, search.ArticleES{
			ID:                article.ID,
			Title:             article.Title,
			Content:           article.Content,
			UserID:            article.UserID,
			Username:          article.Username,
			Tags:              article.Tags,
			Status:            article.Status,
			Views:             article.Views,
			LikeCount:         article.LikeCount,
			CollectCount:      article.CollectCount,
			AuthorFollowCount: article.AuthorFollowCount,
			CategoryName:      article.CategoryName,
			SubCategoryName:   article.SubCategoryName,
			CreateAt:          normalizeESDateTime(article.CreateAt),
			UpdateAt:          normalizeESDateTime(article.UpdateAt),
			AIScore:           article.AIScore,
			UserScore:         article.UserScore,
			AICommentCount:    article.AICommentCount,
			UserCommentCount:  article.UserCommentCount,
		})
	}

	return docs
}

func normalizeESDateTime(value string) string {
	if value == "" {
		return value
	}

	layouts := []string{
		esDateTimeLayout,
		"2006-01-02T15:04:05",
		time.RFC3339,
		time.RFC3339Nano,
		"2006-01-02T15:04:05.000",
		"2006-01-02T15:04:05.000000",
	}
	for _, layout := range layouts {
		if parsed, err := time.ParseInLocation(layout, value, time.Local); err == nil {
			return parsed.Format(esDateTimeLayout)
		}
	}

	return value
}

func loadExistingESArticles(ctx context.Context, svcCtx *svc.ServiceContext) (map[int64]string, error) {
	existingDocs := make(map[int64]string)

	exists, err := svcCtx.ESClient.IndexExists(esArticlesIndexName).Do(ctx)
	if err != nil {
		return nil, logAndWrapError(svcCtx, utils.INDEX_CHECK_ERROR_MESSAGE, err)
	}
	if !exists {
		return existingDocs, nil
	}

	// 使用 Scroll 分批扫描 ES，避免一次性把索引中的所有文档拉回来
	scroll := svcCtx.ESClient.Scroll(esArticlesIndexName).Size(esSyncBatchSize)
	for {
		result, err := scroll.Do(ctx)
		if err == io.EOF {
			break
		}
		if err != nil {
			return nil, logAndWrapError(svcCtx, utils.ES_BULK_SYNC_ERROR_MESSAGE, err)
		}

		for _, hit := range result.Hits.Hits {
			var doc search.ArticleES
			if err := json.Unmarshal(hit.Source, &doc); err != nil {
				return nil, logAndWrapError(svcCtx, utils.ES_BULK_SYNC_ERROR_MESSAGE, err)
			}
			// 这里直接对 ES 中现有文档计算 hash，后面和 DB 生成的新文档做同口径比对
			hashValue, err := hashArticleES(doc)
			if err != nil {
				return nil, logAndWrapError(svcCtx, utils.ES_BULK_SYNC_ERROR_MESSAGE, err)
			}
			existingDocs[doc.ID] = hashValue
		}
	}

	return existingDocs, nil
}

func deleteStaleESArticles(ctx context.Context, svcCtx *svc.ServiceContext, staleDocs map[int64]string) (int, error) {
	if len(staleDocs) == 0 {
		return 0, nil
	}

	// 剩余 staleDocs 的 key 就是“ES 中存在、但 DB 中已不存在的已发布文章”
	ids := make([]int64, 0, len(staleDocs))
	for id := range staleDocs {
		ids = append(ids, id)
	}

	deleted := 0
	for start := 0; start < len(ids); start += esSyncBatchSize {
		end := start + esSyncBatchSize
		if end > len(ids) {
			end = len(ids)
		}

		bulkRequest := svcCtx.ESClient.Bulk()
		for _, id := range ids[start:end] {
			bulkRequest = bulkRequest.Add(
				elastic.NewBulkDeleteRequest().
					Index(esArticlesIndexName).
					Id(fmt.Sprintf("%d", id)),
			)
		}

		// 删除也走 bulk，保持和新增/更新一致的批处理方式
		if err := executeESBulk(ctx, svcCtx, bulkRequest); err != nil {
			return deleted, err
		}
		deleted += end - start
	}

	return deleted, nil
}

func executeESBulk(ctx context.Context, svcCtx *svc.ServiceContext, bulkRequest *elastic.BulkService) error {
	if bulkRequest.NumberOfActions() == 0 {
		return nil
	}

	// 统一封装 bulk 执行和失败处理，避免新增、更新、删除各写一套错误判断
	resp, err := bulkRequest.Do(ctx)
	if err != nil {
		return logAndWrapError(svcCtx, utils.ES_BULK_SYNC_ERROR_MESSAGE, err)
	}

	if !resp.Errors {
		return nil
	}

	for _, item := range resp.Failed() {
		if svcCtx.Logger != nil {
			svcCtx.Logger.Error(fmt.Sprintf(utils.ES_SYNC_FAILURE_DETAILS_MESSAGE, item.Error))
		}
	}
	if svcCtx.Logger != nil {
		svcCtx.Logger.Error(utils.ES_SYNC_HAS_FAILURES_MESSAGE)
	}
	return fmt.Errorf("%s", utils.ES_SYNC_HAS_FAILURES_MESSAGE)
}

func hashArticleES(doc search.ArticleES) (string, error) {
	// 直接对完整文档做 JSON 序列化后计算哈希
	payload, err := json.Marshal(doc)
	if err != nil {
		return "", err
	}

	sum := sha256.Sum256(payload)
	return hex.EncodeToString(sum[:]), nil
}

func logAndWrapError(svcCtx *svc.ServiceContext, message string, err error) error {
	if svcCtx != nil && svcCtx.Logger != nil {
		svcCtx.Logger.Error(fmt.Sprintf("%s: %v", message, err))
	}
	return fmt.Errorf("%s: %w", message, err)
}

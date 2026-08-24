package logic

import (
	"context"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io"
	"time"

	"app/common/client"
	"app/common/constants"
	"app/internal/client/springClient"
	"app/internal/svc"
	"app/model/search"

	"github.com/olivere/elastic/v7"
	"github.com/zeromicro/go-zero/core/mr"
)

const (
	esArticlesIndexName = "articles"
	esSyncBatchSize     = 500
)

type esSyncStats struct {
	Added   int
	Updated int
	Deleted int
}

// normalizeESDate 将日期统一格式化为 ES mapping 要求的 yyyy-MM-dd HH:mm:ss。
// Spring 默认以 ISO 格式返回 LocalDateTime（2025-07-16T23:00:50），与 ES 字段格式不符，
// 此处兜底转换，兼容 ISO（带 T）与目标（空格）两种输入，避免 date_time_parse_exception。
func normalizeESDate(raw string) string {
	if raw == "" {
		return raw
	}
	for _, layout := range []string{
		"2006-01-02T15:04:05",
		time.RFC3339,
		constants.DateTimeFormat,
	} {
		if t, err := time.Parse(layout, raw); err == nil {
			return t.Format(constants.DateTimeFormat)
		}
	}
	return raw
}

// toESDatePtr 将日期字符串归一化为 ES 所需的 *string 指针。空串返回 nil，
// 让 olivere 不写入该字段，避免 ES date 类型收到空串报 cannot parse empty date。
func toESDatePtr(raw string) *string {
	formatted := normalizeESDate(raw)
	if formatted == "" {
		return nil
	}
	return &formatted
}

// SyncArticlesToES 增量同步文章到 ElasticSearch
func SyncArticlesToES(ctx context.Context, svcCtx *svc.ServiceContext) error {
	if svcCtx.ESClient == nil {
		if svcCtx.Logger != nil {
			svcCtx.Logger.Error(constants.ES_CLIENT_NOT_INITIALIZED_MESSAGE)
		}
		return fmt.Errorf("%s", constants.ES_CLIENT_NOT_INITIALIZED_MESSAGE)
	}

	exists, err := svcCtx.ESClient.IndexExists(esArticlesIndexName).Do(ctx)
	if err != nil {
		return logAndWrapError(svcCtx, constants.INDEX_CHECK_ERROR_MESSAGE, err)
	}
	if !exists {
		mapping := constants.ES_INDEX_MAPPING
		_, err := svcCtx.ESClient.CreateIndex(esArticlesIndexName).BodyString(mapping).Do(ctx)
		if err != nil {
			return logAndWrapError(svcCtx, constants.INDEX_CREATION_ERROR_MESSAGE, err)
		}
	}

	// 第一步：先把 ES 中当前已有的文章全部扫出来，构造成 id -> hash 的映射
	existingDocs, err := loadExistingESArticles(ctx, svcCtx)
	if err != nil {
		return err
	}

	// 这些 map 是本次同步过程中的简单本地缓存
	userMap := make(map[int64]string)
	categoryMap := make(map[int64]string)
	subCategoryMap := make(map[int64]string)
	stats := esSyncStats{}
	batchIdx := 0

	// 第二步：通过 Spring 远程调用分页遍历数据库中当前"已发布"的文章
	springCli := svcCtx.SpringClient
	page := 1
	for {
		result, err := springCli.GetPublishedArticles(ctx, page, esSyncBatchSize)
		if err != nil {
			return logAndWrapError(svcCtx, constants.ES_BULK_SYNC_ERROR_MESSAGE, err)
		}
		articles, total, err := springClient.ParseArticlePage(result)
		if err != nil {
			return logAndWrapError(svcCtx, constants.ES_BULK_SYNC_ERROR_MESSAGE, err)
		}
		if len(articles) == 0 {
			break
		}

		batchIdx++
		docs, err := buildArticleESBatchFromRemote(ctx, svcCtx, articles, userMap, categoryMap, subCategoryMap)
		if err != nil {
			return err
		}

		bulkRequest := svcCtx.ESClient.Bulk()
		batchAdded := 0
		batchUpdated := 0
		for _, doc := range docs {
			docHash, err := hashArticleES(doc)
			if err != nil {
				return logAndWrapError(svcCtx, constants.ES_BULK_SYNC_ERROR_MESSAGE, err)
			}

			existingHash, ok := existingDocs[doc.ID]
			if !ok {
				bulkRequest = bulkRequest.Add(
					elastic.NewBulkIndexRequest().
						Index(esArticlesIndexName).
						Id(fmt.Sprintf("%d", doc.ID)).
						Doc(doc),
				)
				batchAdded++
			} else if existingHash != docHash {
				bulkRequest = bulkRequest.Add(
					elastic.NewBulkIndexRequest().
						Index(esArticlesIndexName).
						Id(fmt.Sprintf("%d", doc.ID)).
						Doc(doc),
				)
				batchUpdated++
			}

			delete(existingDocs, doc.ID)
		}

		if bulkRequest.NumberOfActions() > 0 {
			if err := executeESBulk(ctx, svcCtx, bulkRequest); err != nil {
				return err
			}
		}

		stats.Added += batchAdded
		stats.Updated += batchUpdated

		if svcCtx.Logger != nil {
			svcCtx.Logger.Info(fmt.Sprintf(constants.ES_SYNC_BATCH_COMPLETED_MESSAGE, batchIdx, batchAdded, batchUpdated))
		}

		if int64(page*esSyncBatchSize) >= total {
			break
		}
		page++
		time.Sleep(constants.ESSyncBatchDelay)
	}

	// 第三步：删除 ES 中多余的文档
	if len(existingDocs) > 0 {
		deleted, err := deleteStaleESArticles(ctx, svcCtx, existingDocs)
		if err != nil {
			return err
		}
		stats.Deleted = deleted
	}

	if svcCtx.Logger != nil {
		svcCtx.Logger.Info(fmt.Sprintf(constants.ES_INCREMENTAL_SYNC_COMPLETED_MESSAGE, stats.Added, stats.Updated, stats.Deleted))
	}

	if stats.Added == 0 && stats.Updated == 0 && stats.Deleted == 0 && svcCtx.Logger != nil {
		svcCtx.Logger.Info(constants.NO_PUBLISHED_ARTICLES_TO_SYNC_MESSAGE)
	}

	return nil
}

// buildArticleESBatchFromRemote 通过 Spring 远程调用补齐文章 ES 文档所需的关联数据
func buildArticleESBatchFromRemote(
	ctx context.Context,
	svcCtx *svc.ServiceContext,
	articleBatch []springClient.ArticleVO,
	userMap map[int64]string,
	categoryMap map[int64]string,
	subCategoryMap map[int64]string,
) ([]search.ArticleES, error) {
	springCli := svcCtx.SpringClient

	// 收集本批次涉及的主键集合
	userIDs := make([]int64, 0, len(articleBatch))
	subCategoryIDSet := make(map[int64]bool)
	articleIDs := make([]int64, 0, len(articleBatch))

	for _, article := range articleBatch {
		userIDs = append(userIDs, article.UserID)
		if article.SubCategoryID > 0 {
			subCategoryIDSet[int64(article.SubCategoryID)] = true
		}
		articleIDs = append(articleIDs, article.ID)
	}

	// 批量补齐缺失的用户名
	missingUserIDs := make([]int64, 0)
	for _, uid := range userIDs {
		if _, ok := userMap[uid]; !ok {
			missingUserIDs = append(missingUserIDs, uid)
		}
	}
	if len(missingUserIDs) > 0 {
		result, err := springCli.GetUsersByIDs(ctx, missingUserIDs)
		if err != nil {
			if svcCtx.Logger != nil {
				svcCtx.Logger.Error(fmt.Sprintf(constants.BATCH_QUERY_USER_FAIL, err))
			}
		} else {
			users, err := springClient.ParseUserVOs(result)
			if err == nil {
				for _, u := range users {
					userMap[u.ID] = u.Name
				}
			}
		}
	}

	// 批量补齐缺失的子分类名和分类名
	missingSubCategoryIDs := make([]int64, 0)
	for sid := range subCategoryIDSet {
		if _, ok := subCategoryMap[sid]; !ok {
			missingSubCategoryIDs = append(missingSubCategoryIDs, sid)
		}
	}
	if len(missingSubCategoryIDs) > 0 {
		result, err := springCli.GetSubCategoriesByIDs(ctx, missingSubCategoryIDs)
		if err != nil {
			if svcCtx.Logger != nil {
				svcCtx.Logger.Error(fmt.Sprintf(constants.BATCH_QUERY_SUBCATEGORY_FAIL, err))
			}
		} else {
			subCategories, err := springClient.ParseSubCategoryVOs(result)
			if err == nil {
				for _, sc := range subCategories {
					subCategoryMap[sc.ID] = sc.Name
				}
				// 收集需要查询的分类ID
				categoryIDs := make([]int64, 0, len(subCategories))
				for _, sc := range subCategories {
					if _, ok := categoryMap[sc.CategoryID]; !ok {
						categoryIDs = append(categoryIDs, sc.CategoryID)
					}
				}
				if len(categoryIDs) > 0 {
					catResult, catErr := springCli.GetCategoriesByIDs(ctx, categoryIDs)
					if catErr == nil {
						categories, parseErr := springClient.ParseCategoryVOs(catResult)
						if parseErr == nil {
							for _, c := range categories {
								categoryMap[c.ID] = c.Name
							}
						}
					}
				}
				// 建立子分类ID到分类ID的映射，用于后续填充categoryMap
				for _, sc := range subCategories {
					if catName, ok := categoryMap[sc.CategoryID]; ok {
						categoryMap[sc.ID] = catName
					}
				}
			}
		}
	}

	// 批量查询评论评分、点赞数、收藏数、粉丝数（四个独立远程调用并行执行）
	var commentResult, likeResult, collectResult, followResult client.Result
	var commentErr, likeErr, collectErr, followErr error

	_ = mr.Finish(
		func() error {
			commentResult, commentErr = springCli.GetCommentScoresByArticleIDs(ctx, articleIDs)
			return commentErr
		},
		func() error {
			likeResult, likeErr = springCli.GetLikeCountsByArticleIDs(ctx, articleIDs)
			return likeErr
		},
		func() error {
			collectResult, collectErr = springCli.GetCollectCountsByArticleIDs(ctx, articleIDs)
			return collectErr
		},
		func() error {
			followResult, followErr = springCli.GetFollowCountsByUserIDs(ctx, userIDs)
			return followErr
		},
	)

	if commentErr != nil {
		return nil, logAndWrapError(svcCtx, constants.CREATE_MESSAGE_ERROR, commentErr)
	}
	if likeErr != nil {
		return nil, logAndWrapError(svcCtx, constants.LIKE_QUERY_ERROR, likeErr)
	}
	if collectErr != nil {
		return nil, logAndWrapError(svcCtx, constants.COLLECT_QUERY_ERROR, collectErr)
	}
	if followErr != nil {
		return nil, logAndWrapError(svcCtx, constants.FOCUS_QUERY_ERROR, followErr)
	}

	commentScores, _ := springClient.ParseCommentScoresMap(commentResult)
	likeCounts, _ := springClient.ParseCountsMap(likeResult)
	collectCounts, _ := springClient.ParseCountsMap(collectResult)
	authorFollowCounts, _ := springClient.ParseCountsMap(followResult)

	// 组装 ES 文档
	docs := make([]search.ArticleES, 0, len(articleBatch))
	for _, article := range articleBatch {
		scores := commentScores[article.ID]

		aiScore := 0.0
		aiCount := 0
		if aiScoreData, ok := scores["ai"]; ok {
			aiScore = aiScoreData.AverageScore
			aiCount = int(aiScoreData.Count)
		}

		userScore := 0.0
		userCount := 0
		if userScoreData, ok := scores["user"]; ok {
			userScore = userScoreData.AverageScore
			userCount = int(userScoreData.Count)
		}

		docs = append(docs, search.ArticleES{
			ID:                article.ID,
			Title:             article.Title,
			Content:           article.Content,
			UserID:            article.UserID,
			Username:          userMap[article.UserID],
			Tags:              article.Tags,
			Status:            article.Status,
			Views:             article.Views,
			LikeCount:         int(likeCounts[article.ID]),
			CollectCount:      int(collectCounts[article.ID]),
			AuthorFollowCount: int(authorFollowCounts[article.UserID]),
			CategoryName:      categoryMap[int64(article.SubCategoryID)],
			SubCategoryName:   subCategoryMap[int64(article.SubCategoryID)],
			CreateAt:          toESDatePtr(article.CreateAt),
			UpdateAt:          toESDatePtr(article.UpdateAt),
			AIScore:           aiScore,
			UserScore:         userScore,
			AICommentCount:    aiCount,
			UserCommentCount:  userCount,
		})
	}

	return docs, nil
}

func loadExistingESArticles(ctx context.Context, svcCtx *svc.ServiceContext) (map[int64]string, error) {
	existingDocs := make(map[int64]string)

	exists, err := svcCtx.ESClient.IndexExists(esArticlesIndexName).Do(ctx)
	if err != nil {
		return nil, logAndWrapError(svcCtx, constants.INDEX_CHECK_ERROR_MESSAGE, err)
	}
	if !exists {
		return existingDocs, nil
	}

	scroll := svcCtx.ESClient.Scroll(esArticlesIndexName).Size(esSyncBatchSize)
	for {
		result, err := scroll.Do(ctx)
		if err == io.EOF {
			break
		}
		if err != nil {
			return nil, logAndWrapError(svcCtx, constants.ES_BULK_SYNC_ERROR_MESSAGE, err)
		}

		for _, hit := range result.Hits.Hits {
			var doc search.ArticleES
			if err := json.Unmarshal(hit.Source, &doc); err != nil {
				return nil, logAndWrapError(svcCtx, constants.ES_BULK_SYNC_ERROR_MESSAGE, err)
			}
			hashValue, err := hashArticleES(doc)
			if err != nil {
				return nil, logAndWrapError(svcCtx, constants.ES_BULK_SYNC_ERROR_MESSAGE, err)
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

	resp, err := bulkRequest.Do(ctx)
	if err != nil {
		return logAndWrapError(svcCtx, constants.ES_BULK_SYNC_ERROR_MESSAGE, err)
	}

	if !resp.Errors {
		return nil
	}

	for _, item := range resp.Failed() {
		if svcCtx.Logger != nil {
			svcCtx.Logger.Error(fmt.Sprintf(constants.ES_SYNC_FAILURE_DETAILS_MESSAGE, item.Error))
		}
	}
	if svcCtx.Logger != nil {
		svcCtx.Logger.Error(constants.ES_SYNC_HAS_FAILURES_MESSAGE)
	}
	return fmt.Errorf("%s", constants.ES_SYNC_HAS_FAILURES_MESSAGE)
}

func hashArticleES(doc search.ArticleES) (string, error) {
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

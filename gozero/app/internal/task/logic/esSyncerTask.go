package logic

import (
	"context"
	"fmt"
	"time"

	"app/common/utils"
	"app/internal/svc"
	"app/model/articles"
	"app/model/search"

	"github.com/olivere/elastic/v7"
)

// SyncArticlesToES 同步文章到ElasticSearch
func SyncArticlesToES(svcCtx *svc.ServiceContext) error {
	ctx := context.Background()

	// 检查ESClient是否初始化
	if svcCtx.ESClient == nil {
		if svcCtx.Logger != nil {
			svcCtx.Logger.Error(utils.ES_CLIENT_NOT_INITIALIZED_MESSAGE)
		}
		return fmt.Errorf("%s", utils.ES_CLIENT_NOT_INITIALIZED_MESSAGE)
	}

	// 判断索引是否存在
	exists, err := svcCtx.ESClient.IndexExists("articles").Do(ctx)
	if err != nil {
		return logAndWrapError(svcCtx, utils.INDEX_CHECK_ERROR_MESSAGE, err)
	}
	if !exists {
		// 创建索引，指定mapping
		mapping := utils.ES_INDEX_MAPPING
		_, err := svcCtx.ESClient.CreateIndex("articles").BodyString(mapping).Do(ctx)
		if err != nil {
			return logAndWrapError(svcCtx, utils.INDEX_CREATION_ERROR_MESSAGE, err)
		}
	}

	// 删除 articles 索引中的所有旧文档
	_, err = svcCtx.ESClient.DeleteByQuery("articles").
		Query(elastic.NewMatchAllQuery()).
		Do(ctx)
	if err != nil {
		return logAndWrapError(svcCtx, utils.INDEX_DELETION_ERROR_MESSAGE, err)
	}

	userMap := make(map[int64]string)
	categoryMap := make(map[int64]string)
	subCategoryMap := make(map[int64]string)
	const batchSize = 500
	totalSynced := 0
	batchIdx := 0
	err = svcCtx.ArticlesModel.IteratePublishedArticles(ctx, batchSize, func(articles []articles.Articles) error {
		if len(articles) == 0 {
			return nil
		}

		batchIdx++
		totalSynced += len(articles)

		userIDs := make([]int64, 0, len(articles))
		subCategoryIDs := make([]int64, 0, len(articles))
		articleIDs := make([]int64, 0, len(articles))
		for _, a := range articles {
			userIDs = append(userIDs, a.UserId)
			subCategoryIDs = append(subCategoryIDs, int64(a.SubCategoryId))
			articleIDs = append(articleIDs, a.Id)
		}

		for _, uid := range userIDs {
			if _, ok := userMap[uid]; ok {
				continue
			}
			u, err := svcCtx.UserModel.FindOne(ctx, uid)
			if err != nil {
				if svcCtx.Logger != nil {
					svcCtx.Logger.Error(fmt.Sprintf(utils.QUERY_USER_ERROR, uid, err))
				}
				continue
			}
			userMap[uid] = u.Name
		}

		for _, scID := range subCategoryIDs {
			if _, ok := subCategoryMap[scID]; ok {
				continue
			}
			sc, err := svcCtx.SubCategoryModel.FindOne(ctx, scID)
			if err != nil {
				if svcCtx.Logger != nil {
					svcCtx.Logger.Error(fmt.Sprintf(utils.QUERY_SUBCATEGORY_ERROR, scID, err))
				}
				continue
			}
			subCategoryMap[scID] = sc.Name

			if _, ok := categoryMap[scID]; ok {
				continue
			}
			c, err := svcCtx.CategoryModel.FindOne(ctx, int64(sc.CategoryId))
			if err != nil {
				if svcCtx.Logger != nil {
					svcCtx.Logger.Error(fmt.Sprintf(utils.QUERY_CATEGORY_ERROR, sc.CategoryId, err))
				}
				continue
			}
			categoryMap[scID] = c.Name
		}

		commentScores, err := svcCtx.CommentsModel.GetCommentScoresByArticleIDs(ctx, articleIDs)
		if err != nil {
			return logAndWrapError(svcCtx, utils.CREATE_MESSAGE_ERROR, err)
		}
		likeCounts, err := svcCtx.LikesModel.GetLikeCountsByArticleIDs(ctx, articleIDs)
		if err != nil {
			return logAndWrapError(svcCtx, utils.LIKE_QUERY_ERROR, err)
		}
		collectCounts, err := svcCtx.CollectsModel.GetCollectCountsByArticleIDs(ctx, articleIDs)
		if err != nil {
			return logAndWrapError(svcCtx, utils.COLLECT_QUERY_ERROR, err)
		}
		authorFollowCounts, err := svcCtx.FocusModel.GetFollowCountsByUserIDs(ctx, userIDs)
		if err != nil {
			return logAndWrapError(svcCtx, utils.FOCUS_QUERY_ERROR, err)
		}

		bulkRequest := svcCtx.ESClient.Bulk()
		for _, article := range articles {
			scores := commentScores[article.Id]

			// 提取AI和用户评分
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

			likeCount := int64(0)
			if lc, ok := likeCounts[article.Id]; ok {
				likeCount = lc
			}

			collectCount := int64(0)
			if cc, ok := collectCounts[article.Id]; ok {
				collectCount = cc
			}

			authorFollowCount := int64(0)
			if afc, ok := authorFollowCounts[article.UserId]; ok {
				authorFollowCount = afc
			}

			articleES := search.ArticleES{
				ID:                article.Id,
				Title:             article.Title,
				Content:           article.Content,
				UserID:            article.UserId,
				Username:          userMap[article.UserId],
				Tags:              article.Tags,
				Status:            int(article.Status),
				Views:             int(article.Views),
				LikeCount:         int(likeCount),
				CollectCount:      int(collectCount),
				AuthorFollowCount: int(authorFollowCount),
				CategoryName:      categoryMap[int64(article.SubCategoryId)],
				SubCategoryName:   subCategoryMap[int64(article.SubCategoryId)],
				CreateAt:          article.CreateAt.Format("2006-01-02 15:04:05"),
				UpdateAt:          article.UpdateAt.Format("2006-01-02 15:04:05"),
				AIScore:           aiScore,
				UserScore:         userScore,
				AICommentCount:    aiCount,
				UserCommentCount:  userCount,
			}

			req := elastic.NewBulkIndexRequest().
				Index("articles").
				Id(fmt.Sprintf("%d", article.Id)).
				Doc(articleES)
			bulkRequest = bulkRequest.Add(req)
		}

		resp, err := bulkRequest.Do(ctx)
		if err != nil {
			return logAndWrapError(svcCtx, utils.ES_BULK_SYNC_ERROR_MESSAGE, err)
		}

		if resp.Errors {
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

		if svcCtx.Logger != nil {
			svcCtx.Logger.Info(fmt.Sprintf("第 %d 批提交完成，本批 %d 条，累计同步 %d 条", batchIdx, len(articles), totalSynced))
		}

		time.Sleep(500 * time.Millisecond)
		return nil
	})
	if err != nil {
		return err
	}

	if totalSynced == 0 {
		if svcCtx.Logger != nil {
			svcCtx.Logger.Info(utils.NO_PUBLISHED_ARTICLES_TO_SYNC_MESSAGE)
		}
		return nil
	}

	return nil
}

func logAndWrapError(svcCtx *svc.ServiceContext, message string, err error) error {
	if svcCtx != nil && svcCtx.Logger != nil {
		svcCtx.Logger.Error(fmt.Sprintf("%s: %v", message, err))
	}
	return fmt.Errorf("%s: %w", message, err)
}

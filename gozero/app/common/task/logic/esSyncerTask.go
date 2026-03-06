package logic

import (
	"context"
	"fmt"
	"time"

	"app/common/exceptions"
	"app/common/utils"
	"app/internal/svc"
	"app/model/search"

	"github.com/olivere/elastic/v7"
)

// SyncArticlesToES 同步文章到Elasticsearch
func SyncArticlesToES(svcCtx *svc.ServiceContext) {
	ctx := context.Background()

	// 检查ESClient是否初始化
	if svcCtx.ESClient == nil {
		if svcCtx.Logger != nil {
			svcCtx.Logger.Error(utils.ES_CLIENT_NOT_INITIALIZED_MESSAGE)
		}
		return
	}

	// 判断索引是否存在
	exists, err := svcCtx.ESClient.IndexExists("articles").Do(ctx)
	if err != nil {
		panic(exceptions.NewBusinessError(utils.INDEX_CHECK_ERROR_MESSAGE, err.Error()))
	}
	if !exists {
		// 创建索引，指定mapping
		mapping := utils.ES_INDEX_MAPPING
		_, err := svcCtx.ESClient.CreateIndex("articles").BodyString(mapping).Do(ctx)
		if err != nil {
			panic(exceptions.NewBusinessError(utils.INDEX_CREATION_ERROR_MESSAGE, err.Error()))
		}
	}

	// 删除 articles 索引中的所有旧文档
	_, err = svcCtx.ESClient.DeleteByQuery("articles").
		Query(elastic.NewMatchAllQuery()).
		Do(ctx)
	if err != nil {
		panic(exceptions.NewBusinessError(utils.INDEX_DELETION_ERROR_MESSAGE, err.Error()))
	}

	// 从数据库获取所有发布的文章
	articles, err := svcCtx.ArticlesModel.SearchArticles(ctx)
	if err != nil {
		panic(exceptions.NewBusinessError(utils.ARTICLE_QUERY_ERROR, err.Error()))
	}

	if len(articles) == 0 {
		if svcCtx.Logger != nil {
			svcCtx.Logger.Info(utils.NO_PUBLISHED_ARTICLES_TO_SYNC_MESSAGE)
		}
		return
	}

	// 收集用户IDs和子分类IDs
	userIDs := make([]int64, 0, len(articles))
	subCategoryIDs := make([]int64, 0, len(articles))
	articleIDs := make([]int64, 0, len(articles))

	for _, a := range articles {
		userIDs = append(userIDs, a.UserId)
		subCategoryIDs = append(subCategoryIDs, int64(a.SubCategoryId))
		articleIDs = append(articleIDs, a.Id)
	}

	// 查询所有相关用户
	userMap := make(map[int64]string)
	for _, uid := range userIDs {
		u, err := svcCtx.UserModel.FindOne(ctx, uid)
		if err != nil {
			if svcCtx.Logger != nil {
				svcCtx.Logger.Error(fmt.Sprintf(utils.QUERY_USER_ERROR, uid, err))
			}
			continue
		}
		userMap[uid] = u.Name
	}

	// 查询分类信息
	categoryMap := make(map[int64]string)
	subCategoryMap := make(map[int64]string)
	for _, scID := range subCategoryIDs {
		sc, err := svcCtx.SubCategoryModel.FindOne(ctx, scID)
		if err != nil {
			if svcCtx.Logger != nil {
				svcCtx.Logger.Error(fmt.Sprintf(utils.QUERY_SUBCATEGORY_ERROR, scID, err))
			}
			continue
		}
		subCategoryMap[scID] = sc.Name

		// 查询对应的分类
		c, err := svcCtx.CategoryModel.FindOne(ctx, int64(sc.CategoryId))
		if err != nil {
			if svcCtx.Logger != nil {
				svcCtx.Logger.Error(fmt.Sprintf(utils.QUERY_CATEGORY_ERROR, sc.CategoryId, err))
			}
			continue
		}
		categoryMap[scID] = c.Name
	}

	// 批量获取评分数据
	commentScores, err := svcCtx.CommentsModel.GetCommentScoresByArticleIDs(ctx, articleIDs)
	if err != nil {
		panic(exceptions.NewBusinessError(utils.CREATE_MESSAGE_ERROR, err.Error()))
	}
	if svcCtx.Logger != nil {
		svcCtx.Logger.Info(fmt.Sprintf(utils.BULK_FETCH_ARTICLE_RATINGS_COMPLETED_MESSAGE, len(articles)))
	}

	// 批量获取点赞数和收藏数
	likeCounts, err := svcCtx.LikesModel.GetLikeCountsByArticleIDs(ctx, articleIDs)
	if err != nil {
		panic(exceptions.NewBusinessError(utils.LIKE_QUERY_ERROR, err.Error()))
	}

	collectCounts, err := svcCtx.CollectsModel.GetCollectCountsByArticleIDs(ctx, articleIDs)
	if err != nil {
		panic(exceptions.NewBusinessError(utils.COLLECT_QUERY_ERROR, err.Error()))
	}
	if svcCtx.Logger != nil {
		svcCtx.Logger.Info(fmt.Sprintf(utils.BULK_FETCH_ARTICLE_LIKES_COLLECTS_COMPLETED_MESSAGE, len(articles)))
	}

	// 批量获取作者的关注数（粉丝数）
	authorFollowCounts, err := svcCtx.FocusModel.GetFollowCountsByUserIDs(ctx, userIDs)
	if err != nil {
		panic(exceptions.NewBusinessError(utils.FOCUS_QUERY_ERROR, err.Error()))
	}
	if svcCtx.Logger != nil {
		svcCtx.Logger.Info(fmt.Sprintf(utils.BULK_FETCH_AUTHOR_FOLLOWS_COMPLETED_MESSAGE, len(userIDs)))
	}

	// 分批提交ES文档，每批1000条避免资源耗尽
	batchSize := 1000
	totalBatches := (len(articles) + batchSize - 1) / batchSize

	for batchIdx := 0; batchIdx < totalBatches; batchIdx++ {
		start := batchIdx * batchSize
		end := start + batchSize
		if end > len(articles) {
			end = len(articles)
		}

		bulkRequest := svcCtx.ESClient.Bulk()
		for _, article := range articles[start:end] {
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

		resp, err := bulkRequest.Do(context.Background())
		if err != nil {
			panic(exceptions.NewBusinessError(utils.ES_BULK_SYNC_ERROR_MESSAGE, err.Error()))
		}

		if resp.Errors {
			for _, item := range resp.Failed() {
				if svcCtx.Logger != nil {
					svcCtx.Logger.Error(fmt.Sprintf(utils.ES_SYNC_FAILURE_DETAILS_MESSAGE, item.Error))
				}
			}
			panic(exceptions.NewBusinessErrorSame(utils.ES_SYNC_HAS_FAILURES_MESSAGE))
		}

		if svcCtx.Logger != nil {
			svcCtx.Logger.Info(fmt.Sprintf(utils.ES_SYNC_BATCH_SUBMISSION_COMPLETED_MESSAGE, batchIdx+1, totalBatches, end-start))
		}

		// 在批次之间添加延迟，给ES足够时间处理
		if batchIdx < totalBatches-1 {
			time.Sleep(500 * time.Millisecond)
		}
	}
}

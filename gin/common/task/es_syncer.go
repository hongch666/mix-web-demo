package task

import (
	"context"
	"fmt"
	"gin_proj/api/mapper"
	"gin_proj/common/utils"
	"gin_proj/config"
	"gin_proj/entity/po"
	"time"

	"github.com/olivere/elastic"
)

func SyncArticlesToES() {
	// 注入mapper
	articleMapper := mapper.Group.ArticleMapper
	categoryMapper := mapper.Group.CategoryMapper
	userMapper := mapper.Group.UserMapper
	commentMapper := mapper.Group.CommentMapper
	likeMapper := mapper.Group.LikeMapper
	collectMapper := mapper.Group.CollectMapper
	focusMapper := mapper.Group.FocusMapper

	ctx := context.Background()
	// 判断索引是否存在
	exists, err := config.ESClient.IndexExists("articles").Do(ctx)
	if err != nil {
		panic(err.Error())
	}
	if !exists {
		// 创建索引，指定mapping（根据po.Article结构体字段）
		mapping := `{
		"mappings": {
			"properties": {
				"id": { "type": "integer" },
				"title": { "type": "text", "analyzer": "ik_smart", "search_analyzer": "ik_smart" },
				"content": { "type": "text", "analyzer": "ik_smart", "search_analyzer": "ik_smart" },
				"userId": { "type": "integer" },
				"username": { "type": "keyword" },
				"category_name": { "type": "keyword" },
				"sub_category_name": { "type": "keyword" },
				"tags": { "type": "text", "analyzer": "ik_smart", "search_analyzer": "ik_smart" },
				"status": { "type": "integer" },
				"views": { "type": "integer" },
				"likeCount": { "type": "integer" },
				"collectCount": { "type": "integer" },
				"authorFollowCount": { "type": "integer" },
				"create_at": { "type": "date", "format": "yyyy-MM-dd HH:mm:ss" },
				"update_at": { "type": "date", "format": "yyyy-MM-dd HH:mm:ss" },
				"ai_score": { "type": "float" },
				"user_score": { "type": "float" },
				"ai_comment_count": { "type": "integer" },
				"user_comment_count": { "type": "integer" }
			}
		}
		}`
		_, err := config.ESClient.CreateIndex("articles").BodyString(mapping).Do(ctx)
		if err != nil {
			panic(err.Error())
		}
	}
	// 删除 articles 索引中的所有旧文档
	_, err1 := config.ESClient.DeleteByQuery("articles").
		Query(elastic.NewMatchAllQuery()).
		Do(ctx)
	if err1 != nil {
		panic(err1.Error())
	}

	// 获取文章数据
	articles := articleMapper.SearchArticles()

	// 批量获取 user_id
	userIDs := make([]int, 0, len(articles))
	for _, a := range articles {
		userIDs = append(userIDs, int(a.UserID))
	}

	// 查询所有相关用户
	users := userMapper.SearchUserByIds(userIDs)
	userMap := make(map[int]string)
	for _, u := range users {
		userMap[u.ID] = u.Name
	}

	// 批量获取子分类id
	subCategoryIDs := make([]int, 0, len(articles))
	for _, a := range articles {
		subCategoryIDs = append(subCategoryIDs, a.SubCategoryID)
	}

	// 查询所有分类和子分类
	subCategories := categoryMapper.SearchSubCategoriesByIds(subCategoryIDs)

	subCategoryMap := make(map[int]string)
	categoryMap := make(map[int]string)
	for _, sc := range subCategories {
		subCategoryMap[sc.ID] = sc.Name
		category_id := sc.CategoryID
		category := categoryMapper.SearchCategoryById(category_id)
		categoryMap[sc.ID] = category.Name
	}

	// 批量获取所有文章的评分数据
	articleIDs := make([]int64, 0, len(articles))
	articleIDsInt := make([]int, 0, len(articles))
	for _, a := range articles {
		articleIDs = append(articleIDs, int64(a.ID))
		articleIDsInt = append(articleIDsInt, int(a.ID))
	}

	// 调用CommentMapper批量获取评分
	commentScores := commentMapper.GetCommentScoresByArticleIDs(ctx, articleIDs)
	utils.FileLogger.Info(fmt.Sprintf("[ES同步] 批量获取 %d 篇文章的评分信息完成", len(articles)))

	// 批量获取点赞数和收藏数
	likeCounts := likeMapper.GetLikeCountsByArticleIDs(ctx, articleIDsInt)
	collectCounts := collectMapper.GetCollectCountsByArticleIDs(ctx, articleIDsInt)
	utils.FileLogger.Info(fmt.Sprintf("[ES同步] 批量获取 %d 篇文章的点赞和收藏信息完成", len(articles)))

	// 批量获取作者的关注数（粉丝数）
	authorFollowCounts := focusMapper.GetFollowCountsByUserIDs(ctx, userIDs)
	utils.FileLogger.Info(fmt.Sprintf("[ES同步] 批量获取 %d 个作者的关注信息完成", len(userIDs)))

	if len(articles) == 0 {
		panic("没有已发布的文章可同步")
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

		bulkRequest := config.ESClient.Bulk()
		for _, article := range articles[start:end] {
			scores := commentScores[int64(article.ID)]

			// 提取AI和用户评分
			aiScore := 0.0
			aiCount := 0
			if aiScoreData, ok := scores["ai"]; ok {
				aiScore = aiScoreData.AverageScore
				aiCount = aiScoreData.Count
			}

			userScore := 0.0
			userCount := 0
			if userScoreData, ok := scores["user"]; ok {
				userScore = userScoreData.AverageScore
				userCount = userScoreData.Count
			}

			articleES := po.ArticleES{
				ID:                int(article.ID),
				Title:             article.Title,
				Content:           article.Content,
				UserID:            int(article.UserID),
				Username:          userMap[int(article.UserID)],
				Tags:              article.Tags,
				Status:            article.Status,
				Views:             article.Views,
				LikeCount:         likeCounts[int(article.ID)],
				CollectCount:      collectCounts[int(article.ID)],
				AuthorFollowCount: authorFollowCounts[int(article.UserID)],
				CategoryName:      categoryMap[article.SubCategoryID],
				SubCategoryName:   subCategoryMap[article.SubCategoryID],
				CreateAt:          article.CreateAt.Format("2006-01-02 15:04:05"),
				UpdateAt:          article.UpdateAt.Format("2006-01-02 15:04:05"),
				AIScore:           aiScore,
				UserScore:         userScore,
				AICommentCount:    aiCount,
				UserCommentCount:  userCount,
			}
			req := elastic.NewBulkIndexRequest().
				Index("articles").
				Id(fmt.Sprintf("%d", article.ID)).
				Doc(articleES)
			bulkRequest = bulkRequest.Add(req)
		}

		resp, err2 := bulkRequest.Do(context.Background())
		if err2 != nil {
			panic(err2.Error())
		}
		if resp.Errors {
			for _, item := range resp.Failed() {
				utils.FileLogger.Error(fmt.Sprintf("ES同步失败: %+v", item.Error))
			}
			panic("ES同步有失败项")
		}

		utils.FileLogger.Info(fmt.Sprintf("[ES同步] 第 %d/%d 批提交完成，共 %d 条记录", batchIdx+1, totalBatches, end-start))

		// 在批次之间添加延迟，给ES足够时间处理，防止资源耗尽
		if batchIdx < totalBatches-1 {
			time.Sleep(500 * time.Millisecond)
		}
	}
}

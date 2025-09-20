package syncer

import (
	"context"
	"fmt"
	"gin_proj/api/mapper"
	"gin_proj/common/utils"
	"gin_proj/config"
	"gin_proj/entity/po"

	"github.com/olivere/elastic"
)

func SyncArticlesToES() {
	// 注入mapper
	articleMapper := mapper.Group.ArticleMapper
	categoryMapper := mapper.Group.CategoryMapper
	userMapper := mapper.Group.UserMapper

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
				"create_at": { "type": "date", "format": "yyyy-MM-dd HH:mm:ss" },
				"update_at": { "type": "date", "format": "yyyy-MM-dd HH:mm:ss" }
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

	// 批量构建ES文档
	bulkRequest := config.ESClient.Bulk()
	for _, article := range articles {
		articleES := po.ArticleES{
			ID:              int(article.ID),
			Title:           article.Title,
			Content:         article.Content,
			UserID:          int(article.UserID),
			Username:        userMap[int(article.UserID)],
			Tags:            article.Tags,
			Status:          article.Status,
			Views:           article.Views,
			CategoryName:    categoryMap[article.SubCategoryID],
			SubCategoryName: subCategoryMap[article.SubCategoryID],
			CreateAt:        article.CreateAt.Format("2006-01-02 15:04:05"),
			UpdateAt:        article.UpdateAt.Format("2006-01-02 15:04:05"),
		}
		req := elastic.NewBulkIndexRequest().
			Index("articles").
			Id(fmt.Sprintf("%d", article.ID)).
			Doc(articleES)
		bulkRequest = bulkRequest.Add(req)
	}

	if bulkRequest.NumberOfActions() == 0 {
		panic("没有已发布的文章可同步")
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
}

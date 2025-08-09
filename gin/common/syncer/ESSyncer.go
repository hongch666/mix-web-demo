package syncer

import (
	"context"
	"fmt"
	"gin_proj/api/mapper"
	"gin_proj/common/utils"
	"gin_proj/config"
	"gin_proj/entity/po"

	"github.com/gin-gonic/gin"
	"github.com/olivere/elastic"
)

func SyncArticlesToES(c *gin.Context) {
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
	articles := mapper.SearchArticles(c)

	// 批量获取 user_id
	userIDs := make([]int, 0, len(articles))
	for _, a := range articles {
		userIDs = append(userIDs, int(a.UserID))
	}

	// 查询所有相关用户
	users := mapper.SearchUserByIds(c, userIDs)
	userMap := make(map[int]string)
	for _, u := range users {
		userMap[u.ID] = u.Name
	}

	// 批量获取子分类id
	subCategoryIDs := make([]int, 0, len(articles))
	for _, a := range articles {
		subCategoryIDs = append(subCategoryIDs, a.SubCategoryID)
	}

	// 查询所有子分类
	subCategories := mapper.SearchSubCategoriesByIds(c, subCategoryIDs)
	subCategoryMap := make(map[int]string)
	categoryIDSet := make(map[int]struct{})
	for _, sc := range subCategories {
		subCategoryMap[sc.ID] = sc.Name
		if _, exists := categoryIDSet[sc.CategoryID]; !exists {
			categoryIDSet[sc.CategoryID] = struct{}{}
		}
	}

	// 批量获取所有相关的父分类
	categoryIDs := make([]int, 0, len(categoryIDSet))
	for id := range categoryIDSet {
		categoryIDs = append(categoryIDs, id)
	}
	categories := mapper.SearchCategoriesByIds(c, categoryIDs)
	categoryNameMap := make(map[int]string)
	for _, cat := range categories {
		categoryNameMap[cat.ID] = cat.Name
	}

	// 创建一个从子分类ID到父分类名称的映射
	subCategoryToCategoryNameMap := make(map[int]string)
	for _, sc := range subCategories {
		if name, ok := categoryNameMap[sc.CategoryID]; ok {
			subCategoryToCategoryNameMap[sc.ID] = name
		}
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
			CategoryName:    subCategoryToCategoryNameMap[article.SubCategoryID], // 使用映射获取分类名称
			SubCategoryName: subCategoryMap[article.SubCategoryID],
			CreateAt:        article.CreateAt, // 现在是string类型，直接赋值
			UpdateAt:        article.UpdateAt, // 现在是string类型，直接赋值
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

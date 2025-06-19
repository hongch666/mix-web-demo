package syncer

import (
	"context"
	"gin_proj/config"
	"gin_proj/entity/po"
	"log"

	"github.com/olivere/elastic"
)

func SyncArticlesToES() {
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
			"tags": { "type": "text", "analyzer": "ik_smart", "search_analyzer": "ik_smart" },
			"status": { "type": "integer" },
			"views": { "type": "integer" },
			"created_at": { "type": "date", "format": "yyyy-MM-dd HH:mm:ss" },
			"updated_at": { "type": "date", "format": "yyyy-MM-dd HH:mm:ss" }
			}
		}
		}`
		_, err := config.ESClient.CreateIndex("articles").BodyString(mapping).Do(ctx)
		if err != nil {
			panic(err.Error())
		}
	}
	// Step 1: 删除 articles 索引中的所有旧文档
	_, err1 := config.ESClient.DeleteByQuery("articles").
		Query(elastic.NewMatchAllQuery()).
		Do(ctx)
	if err1 != nil {
		panic(err1.Error())
	}

	var articles []po.Article
	if err := config.DB.Where("status = ?", 1).Find(&articles).Error; err != nil {
		panic(err.Error())
	}
	log.Println(articles)
	bulkRequest := config.ESClient.Bulk()

	for _, article := range articles {
		req := elastic.NewBulkIndexRequest().
			Index("articles").
			Id(string(rune(article.ID))).
			Doc(article)
		bulkRequest = bulkRequest.Add(req)
	}

	if bulkRequest.NumberOfActions() == 0 {
		panic("没有可同步的数据")
	}

	_, err2 := bulkRequest.Do(context.Background())
	if err2 != nil {
		panic(err2.Error())
	}
}

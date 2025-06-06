package syncer

import (
	"context"
	"errors"

	"gin_proj/config"
	"gin_proj/po"

	"github.com/olivere/elastic"
)

func SyncArticlesToES() error {
	var articles []po.Article
	if err := config.DB.Where("status = ?", 1).Find(&articles).Error; err != nil {
		return err
	}

	bulkRequest := config.ESClient.Bulk()

	for _, article := range articles {
		req := elastic.NewBulkIndexRequest().
			Index("articles").
			Id(string(rune(article.ID))).
			Doc(article)
		bulkRequest = bulkRequest.Add(req)
	}

	if bulkRequest.NumberOfActions() == 0 {
		return errors.New("没有可同步的数据")
	}

	_, err := bulkRequest.Do(context.Background())
	if err != nil {
		return err
	}

	return nil
}

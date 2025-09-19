package sync

import (
	"context"
	"gin_proj/config"
	"gin_proj/entity/po"

	"gorm.io/gorm"
)

type ArticleMapper struct{}

func (m *ArticleMapper) SearchArticles() []po.Article {
	ctx := context.Background()
	articles, err := gorm.G[po.Article](config.DB).Where("status = ?", 1).Find(ctx)
	if err != nil {
		panic(err.Error())
	}
	return articles
}

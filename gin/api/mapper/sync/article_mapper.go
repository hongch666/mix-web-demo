package sync

import (
	"context"
	"gin_proj/common/exceptions"
	"gin_proj/config"
	"gin_proj/entity/po"

	"gorm.io/gorm"
)

type ArticleMapper struct{}

func (m *ArticleMapper) SearchArticles() []po.Article {
	ctx := context.Background()
	articles, err := gorm.G[po.Article](config.DB).Where("status = ?", 1).Find(ctx)
	if err != nil {
		panic(exceptions.NewBusinessError("文章查询错误", err.Error()))
	}
	return articles
}

// GetArticleViewsByIDs 根据文章ID数组获取对应的阅读量
func (m *ArticleMapper) GetArticleViewsByIDs(ctx context.Context, ids []int) map[int]int {
	result := make(map[int]int)
	articles, err := gorm.G[po.Article](config.DB).Where("id IN ?", ids).Select("id", "views").Find(ctx)
	if err != nil {
		return result
	}

	for _, article := range articles {
		result[int(article.ID)] = article.Views
	}

	return result
}

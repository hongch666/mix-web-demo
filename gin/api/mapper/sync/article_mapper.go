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

// GetArticleLikeCounts 根据文章ID数组获取点赞数
func (m *ArticleMapper) GetArticleLikeCounts(ctx context.Context, ids []int) map[int]int {
	likeMapper := &LikeMapper{}
	return likeMapper.GetLikeCountsByArticleIDs(ctx, ids)
}

// GetArticleCollectCounts 根据文章ID数组获取收藏数
func (m *ArticleMapper) GetArticleCollectCounts(ctx context.Context, ids []int) map[int]int {
	collectMapper := &CollectMapper{}
	return collectMapper.GetCollectCountsByArticleIDs(ctx, ids)
}

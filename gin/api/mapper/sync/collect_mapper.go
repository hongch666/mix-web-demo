package sync

import (
	"context"
	"gin_proj/config"
	"gin_proj/entity/po"

	"gorm.io/gorm"
)

type CollectMapper struct{}

// GetCollectCountByArticleID 根据文章ID获取收藏数
func (m *CollectMapper) GetCollectCountByArticleID(ctx context.Context, articleID int) int {
	count, err := gorm.G[po.Collect](config.DB).Where("article_id = ?", articleID).Count(ctx, "*")
	if err != nil {
		return 0
	}
	return int(count)
}

// GetCollectCountsByArticleIDs 根据文章ID数组批量获取收藏数
func (m *CollectMapper) GetCollectCountsByArticleIDs(ctx context.Context, articleIDs []int) map[int]int {
	result := make(map[int]int)
	type CountResult struct {
		ArticleID int `gorm:"column:article_id"`
		Count     int `gorm:"column:count"`
	}
	var counts []CountResult
	err := config.DB.Model(&po.Collect{}).
		Where("article_id IN ?", articleIDs).
		Select("article_id, count(*) as count").
		Group("article_id").
		Scan(&counts).Error
	if err != nil {
		return result
	}

	for _, item := range counts {
		result[item.ArticleID] = item.Count
	}

	return result
}

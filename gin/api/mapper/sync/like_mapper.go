package sync

import (
	"context"
	"gin_proj/common/exceptions"
	"gin_proj/common/utils"
	"gin_proj/config"
	"gin_proj/entity/po"

	"gorm.io/gorm"
)

type LikeMapper struct{}

// GetLikeCountByArticleID 根据文章ID获取点赞数
func (m *LikeMapper) GetLikeCountByArticleID(ctx context.Context, articleID int) int {
	count, err := gorm.G[po.Like](config.DB).Where("article_id = ?", articleID).Count(ctx, "*")
	if err != nil {
		panic(exceptions.NewBusinessError(utils.LIKE_QUERY_ERROR, err.Error()))
	}
	return int(count)
}

// GetLikeCountsByArticleIDs 根据文章ID数组批量获取点赞数
func (m *LikeMapper) GetLikeCountsByArticleIDs(ctx context.Context, articleIDs []int) map[int]int {
	result := make(map[int]int)
	type CountResult struct {
		ArticleID int `gorm:"column:article_id"`
		Count     int `gorm:"column:count"`
	}
	var counts []CountResult
	err := config.DB.Model(&po.Like{}).
		Where("article_id IN ?", articleIDs).
		Select("article_id, count(*) as count").
		Group("article_id").
		Scan(&counts).Error
	if err != nil {
		panic(exceptions.NewBusinessError(utils.LIKE_QUERY_ERROR, err.Error()))
	}

	for _, item := range counts {
		result[item.ArticleID] = item.Count
	}

	return result
}

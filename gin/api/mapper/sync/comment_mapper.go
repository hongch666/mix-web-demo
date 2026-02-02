package sync

import (
	"context"
	"fmt"

	"github.com/hongch666/mix-web-demo/gin/common/exceptions"
	"github.com/hongch666/mix-web-demo/gin/common/utils"
	"github.com/hongch666/mix-web-demo/gin/config"
)

type CommentMapper struct{}

// CommentScore 评论评分统计信息
type CommentScore struct {
	AverageScore float64
	Count        int
}

// GetCommentScoresByArticleIDs 批量获取文章的AI和用户评分
// 根据users表的role字段区分：role='ai' 为AI评分，其他为用户评分
// 返回格式: map[articleID] -> map[scoreType] -> CommentScore
func (m *CommentMapper) GetCommentScoresByArticleIDs(ctx context.Context, articleIDs []int64) map[int64]map[string]*CommentScore {
	result := make(map[int64]map[string]*CommentScore)
	if len(articleIDs) == 0 {
		return result
	}

	// 初始化map
	for _, id := range articleIDs {
		result[id] = make(map[string]*CommentScore)
	}

	utils.FileLogger.Info(fmt.Sprintf(utils.RATING_QUERY_START, len(articleIDs)))

	// 从MySQL comments表联合users表查询评分信息
	// 根据users表的role字段区分：role='ai' 为AI评分，其他为用户评分
	query := utils.COMMENT_RATING_QUERY

	type QueryResult struct {
		ArticleID    int64   `gorm:"column:article_id"`
		RoleType     string  `gorm:"column:role_type"`
		AvgStar      float64 `gorm:"column:avg_star"`
		CommentCount int     `gorm:"column:comment_count"`
	}

	var results []QueryResult

	// 执行查询
	if err := config.DB.WithContext(ctx).Raw(query, articleIDs).Scan(&results).Error; err != nil {
		panic(exceptions.NewBusinessError(utils.RATING_QUERY_MYSQL_ERROR, err.Error()))
	}

	utils.FileLogger.Info(fmt.Sprintf(utils.RATING_QUERY_COMPLETED, len(results)))
	// 解析查询结果
	for _, item := range results {
		if _, exists := result[item.ArticleID]; !exists {
			result[item.ArticleID] = make(map[string]*CommentScore)
		}

		result[item.ArticleID][item.RoleType] = &CommentScore{
			AverageScore: item.AvgStar,
			Count:        item.CommentCount,
		}

		utils.FileLogger.Debug(fmt.Sprintf(
			utils.RATING_QUERY_RESULT_DEBUG,
			item.ArticleID, item.RoleType, item.AvgStar, item.CommentCount,
		))
	}

	return result
}

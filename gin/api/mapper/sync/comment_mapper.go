package sync

import (
	"context"
	"fmt"
	"gin_proj/common/utils"
	"gin_proj/config"
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

	utils.FileLogger.Info(fmt.Sprintf("[评分查询] 开始从MySQL查询 %d 篇文章的评分信息", len(articleIDs)))

	// 从MySQL comments表联合users表查询评分信息
	// 根据users表的role字段区分：role='ai' 为AI评分，其他为用户评分
	query := `
		SELECT 
			c.article_id,
			CASE WHEN u.role = 'ai' THEN 'ai' ELSE 'user' END as role_type,
			AVG(c.star) as avg_star,
			COUNT(*) as comment_count
		FROM comments c
		LEFT JOIN user u ON c.user_id = u.id
		WHERE c.article_id IN (?) AND c.star > 0
		GROUP BY c.article_id, role_type
	`

	type QueryResult struct {
		ArticleID    int64   `gorm:"column:article_id"`
		RoleType     string  `gorm:"column:role_type"`
		AvgStar      float64 `gorm:"column:avg_star"`
		CommentCount int     `gorm:"column:comment_count"`
	}

	var results []QueryResult

	// 执行查询
	if err := config.DB.WithContext(ctx).Raw(query, articleIDs).Scan(&results).Error; err != nil {
		// 日志记录错误但不中断，返回空评分
		utils.FileLogger.Error(fmt.Sprintf("[评分查询] MySQL查询失败: %v", err))
		return result
	}

	utils.FileLogger.Info(fmt.Sprintf("[评分查询] MySQL查询完成，共获取 %d 条评分记录", len(results)))

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
			"[评分查询] 文章ID:%d | 类型:%s | 平均评分:%.2f | 评论数:%d",
			item.ArticleID, item.RoleType, item.AvgStar, item.CommentCount,
		))
	}

	return result
}

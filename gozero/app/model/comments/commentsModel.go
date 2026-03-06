package comments

import (
	"app/model"
	"context"

	"gorm.io/gorm"
)

var _ CommentsModel = (*customCommentsModel)(nil)

type CommentScore struct {
	AverageScore float64
	Count        int64
}

type (
	// CommentsModel is an interface to be customized, add more methods here,
	// and implement the added methods in customCommentsModel.
	CommentsModel interface {
		Insert(ctx context.Context, data *Comments) error
		FindOne(ctx context.Context, id int64) (*Comments, error)
		Update(ctx context.Context, data *Comments) error
		Delete(ctx context.Context, id int64) error
		GetCommentCountByArticleID(ctx context.Context, articleID int64) (int64, error)
		GetCommentCountsByArticleIDs(ctx context.Context, articleIDs []int64) (map[int64]int64, error)
		GetCommentRateByArticleID(ctx context.Context, articleID int64) (float64, error)
		GetCommentRatesByArticleIDs(ctx context.Context, articleIDs []int64) (map[int64]float64, error)
		GetCommentScoresByArticleIDs(ctx context.Context, articleIDs []int64) (map[int64]map[string]*CommentScore, error)
	}

	customCommentsModel struct {
		crud *model.GormCrud[Comments]
	}
)

// NewCommentsModel returns a model for the database table.
func NewCommentsModel(db *gorm.DB) CommentsModel {
	return &customCommentsModel{
		crud: model.NewGormCrud[Comments](db, "comments"),
	}
}

func (m *customCommentsModel) Insert(ctx context.Context, data *Comments) error {
	return m.crud.Insert(ctx, data)
}

func (m *customCommentsModel) FindOne(ctx context.Context, id int64) (*Comments, error) {
	return m.crud.FindOne(ctx, id)
}

func (m *customCommentsModel) Update(ctx context.Context, data *Comments) error {
	return m.crud.Update(ctx, data.Id, data)
}

func (m *customCommentsModel) Delete(ctx context.Context, id int64) error {
	return m.crud.Delete(ctx, id)
}

func (m *customCommentsModel) GetCommentCountByArticleID(ctx context.Context, articleID int64) (int64, error) {
	db, err := m.crud.Query(ctx)
	if err != nil {
		return 0, err
	}
	var count int64
	err = db.Where("article_id = ?", articleID).Count(&count).Error
	return count, err
}

func (m *customCommentsModel) GetCommentCountsByArticleIDs(ctx context.Context, articleIDs []int64) (map[int64]int64, error) {
	result := make(map[int64]int64)
	if len(articleIDs) == 0 {
		return result, nil
	}
	db, err := m.crud.Query(ctx)
	if err != nil {
		return nil, err
	}
	var rows []struct {
		ArticleID int64 `gorm:"column:article_id"`
		Count     int64 `gorm:"column:count"`
	}
	err = db.Select("article_id, count(*) as count").Where("article_id IN ?", articleIDs).Group("article_id").Scan(&rows).Error
	if err != nil {
		return nil, err
	}
	for _, row := range rows {
		result[row.ArticleID] = row.Count
	}
	return result, nil
}

func (m *customCommentsModel) GetCommentRateByArticleID(ctx context.Context, articleID int64) (float64, error) {
	db, err := m.crud.Query(ctx)
	if err != nil {
		return 0, err
	}
	var rate float64
	err = db.Model(&Comments{}).Select("COALESCE(AVG(star),0)").Where("article_id = ?", articleID).Scan(&rate).Error
	return rate, err
}

func (m *customCommentsModel) GetCommentRatesByArticleIDs(ctx context.Context, articleIDs []int64) (map[int64]float64, error) {
	result := make(map[int64]float64)
	if len(articleIDs) == 0 {
		return result, nil
	}
	db, err := m.crud.Query(ctx)
	if err != nil {
		return nil, err
	}
	var rows []struct {
		ArticleID int64   `gorm:"column:article_id"`
		Rate      float64 `gorm:"column:rate"`
	}
	err = db.Model(&Comments{}).
		Select("article_id, COALESCE(AVG(star),0) as rate").
		Where("article_id IN ?", articleIDs).
		Group("article_id").
		Scan(&rows).Error
	if err != nil {
		return nil, err
	}
	for _, row := range rows {
		result[row.ArticleID] = row.Rate
	}
	return result, nil
}

func (m *customCommentsModel) GetCommentScoresByArticleIDs(ctx context.Context, articleIDs []int64) (map[int64]map[string]*CommentScore, error) {
	result := make(map[int64]map[string]*CommentScore)
	if len(articleIDs) == 0 {
		return result, nil
	}

	for _, articleID := range articleIDs {
		result[articleID] = make(map[string]*CommentScore)
	}

	db, err := m.crud.Query(ctx)
	if err != nil {
		return nil, err
	}

	query := `
		SELECT
			c.article_id,
			CASE WHEN u.role = 'ai' THEN 'ai' ELSE 'user' END AS role_type,
			AVG(c.star) AS avg_star,
			COUNT(*) AS comment_count
		FROM comments c
		LEFT JOIN user u ON c.user_id = u.id
		WHERE c.article_id IN ? AND c.star > 0
		GROUP BY c.article_id, role_type
	`

	var rows []struct {
		ArticleID    int64   `gorm:"column:article_id"`
		RoleType     string  `gorm:"column:role_type"`
		AvgStar      float64 `gorm:"column:avg_star"`
		CommentCount int64   `gorm:"column:comment_count"`
	}

	err = db.Raw(query, articleIDs).Scan(&rows).Error
	if err != nil {
		return nil, err
	}

	for _, row := range rows {
		if _, exists := result[row.ArticleID]; !exists {
			result[row.ArticleID] = make(map[string]*CommentScore)
		}
		result[row.ArticleID][row.RoleType] = &CommentScore{
			AverageScore: row.AvgStar,
			Count:        row.CommentCount,
		}
	}

	return result, nil
}

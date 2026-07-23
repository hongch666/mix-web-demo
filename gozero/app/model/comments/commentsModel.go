package comments

import (
	"context"
	"fmt"
	"strings"

	"app/common/constants"
	"github.com/zeromicro/go-zero/core/stores/sqlx"
)

var _ CommentsModel = (*customCommentsModel)(nil)

type CommentScore struct {
	AverageScore float64
	Count        int64
}
type (
	CommentsModel interface {
		Insert(context.Context, *Comments) error
		FindOne(context.Context, int64) (*Comments, error)
		Update(context.Context, *Comments) error
		Delete(context.Context, int64) error
		GetCommentCountByArticleID(context.Context, int64) (int64, error)
		GetCommentCountsByArticleIDs(context.Context, []int64) (map[int64]int64, error)
		GetCommentRateByArticleID(context.Context, int64) (float64, error)
		GetCommentRatesByArticleIDs(context.Context, []int64) (map[int64]float64, error)
		GetCommentScoresByArticleIDs(context.Context, []int64) (map[int64]map[string]*CommentScore, error)
	}
	customCommentsModel struct {
		conn      sqlx.SqlConn
		baseModel *defaultCommentsModel
	}
)

func NewCommentsModel(conn sqlx.SqlConn) CommentsModel {
	return &customCommentsModel{conn: conn, baseModel: newCommentsModel(conn)}
}
func (m *customCommentsModel) Insert(ctx context.Context, data *Comments) error {
	_, err := m.baseModel.Insert(ctx, data)
	return err
}
func (m *customCommentsModel) FindOne(ctx context.Context, id int64) (*Comments, error) {
	return m.baseModel.FindOne(ctx, id)
}
func (m *customCommentsModel) Update(ctx context.Context, data *Comments) error {
	return m.baseModel.Update(ctx, data)
}
func (m *customCommentsModel) Delete(ctx context.Context, id int64) error {
	return m.baseModel.Delete(ctx, id)
}
func (m *customCommentsModel) GetCommentCountByArticleID(ctx context.Context, articleID int64) (int64, error) {
	var count int64
	err := m.conn.QueryRowCtx(ctx, &count, fmt.Sprintf("select count(*) from %s where article_id = ?", m.baseModel.table), articleID)
	return count, err
}
func (m *customCommentsModel) GetCommentCountsByArticleIDs(ctx context.Context, ids []int64) (map[int64]int64, error) {
	result := make(map[int64]int64)
	if len(ids) == 0 {
		return result, nil
	}
	args := toArgs(ids)
	var rows []struct {
		ArticleID int64 `db:"article_id"`
		Count     int64 `db:"count"`
	}
	query := fmt.Sprintf("select article_id, count(*) as count from %s where article_id in (%s) group by article_id", m.baseModel.table, placeholders(len(ids)))
	if err := m.conn.QueryRowsCtx(ctx, &rows, query, args...); err != nil {
		return nil, err
	}
	for _, row := range rows {
		result[row.ArticleID] = row.Count
	}
	return result, nil
}
func (m *customCommentsModel) GetCommentRateByArticleID(ctx context.Context, articleID int64) (float64, error) {
	var rate float64
	err := m.conn.QueryRowCtx(ctx, &rate, fmt.Sprintf("select coalesce(avg(star), 0) from %s where article_id = ?", m.baseModel.table), articleID)
	return rate, err
}
func (m *customCommentsModel) GetCommentRatesByArticleIDs(ctx context.Context, ids []int64) (map[int64]float64, error) {
	result := make(map[int64]float64)
	if len(ids) == 0 {
		return result, nil
	}
	var rows []struct {
		ArticleID int64   `db:"article_id"`
		Rate      float64 `db:"rate"`
	}
	query := fmt.Sprintf("select article_id, coalesce(avg(star), 0) as rate from %s where article_id in (%s) group by article_id", m.baseModel.table, placeholders(len(ids)))
	if err := m.conn.QueryRowsCtx(ctx, &rows, query, toArgs(ids)...); err != nil {
		return nil, err
	}
	for _, row := range rows {
		result[row.ArticleID] = row.Rate
	}
	return result, nil
}
func (m *customCommentsModel) GetCommentScoresByArticleIDs(ctx context.Context, ids []int64) (map[int64]map[string]*CommentScore, error) {
	result := make(map[int64]map[string]*CommentScore, len(ids))
	if len(ids) == 0 {
		return result, nil
	}
	for _, id := range ids {
		result[id] = make(map[string]*CommentScore)
	}
	query := strings.Replace(constants.COMMENT_RATING_QUERY, "IN (?)", fmt.Sprintf("IN (%s)", placeholders(len(ids))), 1)
	var rows []struct {
		ArticleID    int64   `db:"article_id"`
		RoleType     string  `db:"role_type"`
		AvgStar      float64 `db:"avg_star"`
		CommentCount int64   `db:"comment_count"`
	}
	if err := m.conn.QueryRowsCtx(ctx, &rows, query, toArgs(ids)...); err != nil {
		return nil, err
	}
	for _, row := range rows {
		result[row.ArticleID][row.RoleType] = &CommentScore{AverageScore: row.AvgStar, Count: row.CommentCount}
	}
	return result, nil
}
func placeholders(size int) string { return strings.TrimRight(strings.Repeat("?,", size), ",") }
func toArgs(ids []int64) []any {
	args := make([]any, len(ids))
	for i, id := range ids {
		args[i] = id
	}
	return args
}

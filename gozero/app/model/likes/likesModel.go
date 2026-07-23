package likes

import (
	"context"
	"fmt"
	"strings"

	"github.com/zeromicro/go-zero/core/stores/sqlx"
)

var _ LikesModel = (*customLikesModel)(nil)

type (
	LikesModel interface {
		Insert(context.Context, *Likes) error
		FindOne(context.Context, int64) (*Likes, error)
		Update(context.Context, *Likes) error
		Delete(context.Context, int64) error
		FindOneByArticleIdUserId(context.Context, int64, int64) (*Likes, error)
		GetLikeCountByArticleID(context.Context, int64) (int64, error)
		GetLikeCountsByArticleIDs(context.Context, []int64) (map[int64]int64, error)
	}
	customLikesModel struct {
		conn      sqlx.SqlConn
		baseModel *defaultLikesModel
	}
)

func NewLikesModel(conn sqlx.SqlConn) LikesModel {
	return &customLikesModel{conn: conn, baseModel: newLikesModel(conn)}
}
func (m *customLikesModel) Insert(ctx context.Context, data *Likes) error {
	_, err := m.baseModel.Insert(ctx, data)
	return err
}
func (m *customLikesModel) FindOne(ctx context.Context, id int64) (*Likes, error) {
	return m.baseModel.FindOne(ctx, id)
}
func (m *customLikesModel) Update(ctx context.Context, data *Likes) error {
	return m.baseModel.Update(ctx, data)
}
func (m *customLikesModel) Delete(ctx context.Context, id int64) error {
	return m.baseModel.Delete(ctx, id)
}
func (m *customLikesModel) FindOneByArticleIdUserId(ctx context.Context, articleID, userID int64) (*Likes, error) {
	return m.baseModel.FindOneByArticleIdUserId(ctx, articleID, userID)
}
func (m *customLikesModel) GetLikeCountByArticleID(ctx context.Context, articleID int64) (int64, error) {
	var count int64
	err := m.conn.QueryRowCtx(ctx, &count, fmt.Sprintf("select count(*) from %s where article_id = ?", m.baseModel.table), articleID)
	return count, err
}
func (m *customLikesModel) GetLikeCountsByArticleIDs(ctx context.Context, ids []int64) (map[int64]int64, error) {
	result := make(map[int64]int64)
	if len(ids) == 0 {
		return result, nil
	}
	args := make([]any, len(ids))
	for i, id := range ids {
		args[i] = id
	}
	var rows []struct {
		ArticleID int64 `db:"article_id"`
		Count     int64 `db:"count"`
	}
	query := fmt.Sprintf("select article_id, count(*) as count from %s where article_id in (%s) group by article_id", m.baseModel.table, strings.TrimRight(strings.Repeat("?,", len(ids)), ","))
	if err := m.conn.QueryRowsCtx(ctx, &rows, query, args...); err != nil {
		return nil, err
	}
	for _, row := range rows {
		result[row.ArticleID] = row.Count
	}
	return result, nil
}

package articles

import (
	"context"
	"fmt"
	"strings"

	"github.com/zeromicro/go-zero/core/stores/sqlx"
)

var _ ArticlesModel = (*customArticlesModel)(nil)

type (
	ArticlesModel interface {
		Insert(context.Context, *Articles) error
		FindOne(context.Context, int64) (*Articles, error)
		Update(context.Context, *Articles) error
		Delete(context.Context, int64) error
		SearchArticles(context.Context) ([]Articles, error)
		IteratePublishedArticles(context.Context, int, func([]Articles) error) error
		GetArticleViewsByIDs(context.Context, []int64) (map[int64]int64, error)
	}
	customArticlesModel struct {
		conn      sqlx.SqlConn
		baseModel *defaultArticlesModel
	}
)

func NewArticlesModel(conn sqlx.SqlConn) ArticlesModel {
	return &customArticlesModel{conn: conn, baseModel: newArticlesModel(conn)}
}
func (m *customArticlesModel) Insert(ctx context.Context, data *Articles) error {
	_, err := m.baseModel.Insert(ctx, data)
	return err
}
func (m *customArticlesModel) FindOne(ctx context.Context, id int64) (*Articles, error) {
	return m.baseModel.FindOne(ctx, id)
}
func (m *customArticlesModel) Update(ctx context.Context, data *Articles) error {
	return m.baseModel.Update(ctx, data)
}
func (m *customArticlesModel) Delete(ctx context.Context, id int64) error {
	return m.baseModel.Delete(ctx, id)
}
func (m *customArticlesModel) SearchArticles(ctx context.Context) ([]Articles, error) {
	var articles []Articles
	err := m.IteratePublishedArticles(ctx, 500, func(batch []Articles) error { articles = append(articles, batch...); return nil })
	return articles, err
}
func (m *customArticlesModel) IteratePublishedArticles(ctx context.Context, batchSize int, handler func([]Articles) error) error {
	if batchSize <= 0 {
		batchSize = 500
	}
	var lastID int64
	for {
		var batch []Articles
		query := fmt.Sprintf("select %s from %s where `status` = ? and `id` > ? order by `id` asc limit ?", articlesRows, m.baseModel.table)
		if err := m.conn.QueryRowsCtx(ctx, &batch, query, 1, lastID, batchSize); err != nil {
			return err
		}
		if len(batch) == 0 {
			return nil
		}
		if err := handler(batch); err != nil {
			return err
		}
		lastID = batch[len(batch)-1].Id
	}
}
func (m *customArticlesModel) GetArticleViewsByIDs(ctx context.Context, ids []int64) (map[int64]int64, error) {
	result := make(map[int64]int64)
	if len(ids) == 0 {
		return result, nil
	}
	args := make([]any, len(ids))
	for i, id := range ids {
		args[i] = id
	}
	var rows []struct {
		Id    int64 `db:"id"`
		Views int64 `db:"views"`
	}
	query := fmt.Sprintf("select `id`, `views` from %s where `id` in (%s)", m.baseModel.table, strings.TrimRight(strings.Repeat("?,", len(ids)), ","))
	if err := m.conn.QueryRowsCtx(ctx, &rows, query, args...); err != nil {
		return nil, err
	}
	for _, row := range rows {
		result[row.Id] = row.Views
	}
	return result, nil
}

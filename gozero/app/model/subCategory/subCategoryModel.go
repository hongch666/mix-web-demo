package subCategory

import (
	"context"
	"fmt"
	"strings"

	"github.com/zeromicro/go-zero/core/stores/sqlx"
)

var _ SubCategoryModel = (*customSubCategoryModel)(nil)

type (
	SubCategoryModel interface {
		Insert(ctx context.Context, data *SubCategory) error
		FindOne(ctx context.Context, id int64) (*SubCategory, error)
		Update(ctx context.Context, data *SubCategory) error
		Delete(ctx context.Context, id int64) error
		SearchSubCategoriesByIds(ctx context.Context, subCategoryIDs []int64) ([]SubCategory, error)
	}
	customSubCategoryModel struct {
		conn      sqlx.SqlConn
		baseModel *defaultSubCategoryModel
	}
)

func NewSubCategoryModel(conn sqlx.SqlConn) SubCategoryModel {
	return &customSubCategoryModel{conn: conn, baseModel: newSubCategoryModel(conn)}
}
func (m *customSubCategoryModel) Insert(ctx context.Context, data *SubCategory) error {
	_, err := m.baseModel.Insert(ctx, data)
	return err
}
func (m *customSubCategoryModel) FindOne(ctx context.Context, id int64) (*SubCategory, error) {
	return m.baseModel.FindOne(ctx, id)
}
func (m *customSubCategoryModel) Update(ctx context.Context, data *SubCategory) error {
	return m.baseModel.Update(ctx, data)
}
func (m *customSubCategoryModel) Delete(ctx context.Context, id int64) error {
	return m.baseModel.Delete(ctx, id)
}
func (m *customSubCategoryModel) SearchSubCategoriesByIds(ctx context.Context, ids []int64) ([]SubCategory, error) {
	if len(ids) == 0 {
		return []SubCategory{}, nil
	}
	args := make([]any, len(ids))
	for i, id := range ids {
		args[i] = id
	}
	query := fmt.Sprintf("select %s from %s where `id` in (%s)", subCategoryRows, m.baseModel.table, strings.TrimRight(strings.Repeat("?,", len(ids)), ","))
	var items []SubCategory
	err := m.conn.QueryRowsCtx(ctx, &items, query, args...)
	return items, err
}

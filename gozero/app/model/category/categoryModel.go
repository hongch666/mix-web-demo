package category

import (
	"context"

	"github.com/zeromicro/go-zero/core/stores/sqlx"
)

var _ CategoryModel = (*customCategoryModel)(nil)

type (
	CategoryModel interface {
		Insert(ctx context.Context, data *Category) error
		FindOne(ctx context.Context, id int64) (*Category, error)
		Update(ctx context.Context, data *Category) error
		Delete(ctx context.Context, id int64) error
		SearchCategoryById(ctx context.Context, categoryID int64) (*Category, error)
	}

	customCategoryModel struct{ baseModel *defaultCategoryModel }
)

func NewCategoryModel(conn sqlx.SqlConn) CategoryModel {
	return &customCategoryModel{baseModel: newCategoryModel(conn)}
}
func (m *customCategoryModel) Insert(ctx context.Context, data *Category) error {
	_, err := m.baseModel.Insert(ctx, data)
	return err
}
func (m *customCategoryModel) FindOne(ctx context.Context, id int64) (*Category, error) {
	return m.baseModel.FindOne(ctx, id)
}
func (m *customCategoryModel) Update(ctx context.Context, data *Category) error {
	return m.baseModel.Update(ctx, data)
}
func (m *customCategoryModel) Delete(ctx context.Context, id int64) error {
	return m.baseModel.Delete(ctx, id)
}
func (m *customCategoryModel) SearchCategoryById(ctx context.Context, categoryID int64) (*Category, error) {
	return m.FindOne(ctx, categoryID)
}

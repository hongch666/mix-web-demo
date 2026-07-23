package categoryReference

import (
	"context"

	"github.com/zeromicro/go-zero/core/stores/sqlx"
)

var _ CategoryReferenceModel = (*customCategoryReferenceModel)(nil)

type (
	CategoryReferenceModel interface {
		Insert(ctx context.Context, data *CategoryReference) error
		FindOne(ctx context.Context, id int64) (*CategoryReference, error)
		Update(ctx context.Context, data *CategoryReference) error
		Delete(ctx context.Context, id int64) error
	}
	customCategoryReferenceModel struct {
		baseModel *defaultCategoryReferenceModel
	}
)

func NewCategoryReferenceModel(conn sqlx.SqlConn) CategoryReferenceModel {
	return &customCategoryReferenceModel{baseModel: newCategoryReferenceModel(conn)}
}
func (m *customCategoryReferenceModel) Insert(ctx context.Context, data *CategoryReference) error {
	_, err := m.baseModel.Insert(ctx, data)
	return err
}
func (m *customCategoryReferenceModel) FindOne(ctx context.Context, id int64) (*CategoryReference, error) {
	return m.baseModel.FindOne(ctx, id)
}
func (m *customCategoryReferenceModel) Update(ctx context.Context, data *CategoryReference) error {
	return m.baseModel.Update(ctx, data)
}
func (m *customCategoryReferenceModel) Delete(ctx context.Context, id int64) error {
	return m.baseModel.Delete(ctx, id)
}

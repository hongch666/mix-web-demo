package categoryReference

import (
	"context"

	"app/model"
	"gorm.io/gorm"
)

var _ CategoryReferenceModel = (*customCategoryReferenceModel)(nil)

type (
	// CategoryReferenceModel is an interface to be customized, add more methods here,
	// and implement the added methods in customCategoryReferenceModel.
	CategoryReferenceModel interface {
		Insert(ctx context.Context, data *CategoryReference) error
		FindOne(ctx context.Context, id int64) (*CategoryReference, error)
		Update(ctx context.Context, data *CategoryReference) error
		Delete(ctx context.Context, id int64) error
	}

	customCategoryReferenceModel struct {
		crud *model.GormCrud[CategoryReference]
	}
)

// NewCategoryReferenceModel returns a model for the database table.
func NewCategoryReferenceModel(db *gorm.DB) CategoryReferenceModel {
	return &customCategoryReferenceModel{
		crud: model.NewGormCrud[CategoryReference](db, "category_reference"),
	}
}

func (m *customCategoryReferenceModel) Insert(ctx context.Context, data *CategoryReference) error {
	return m.crud.Insert(ctx, data)
}

func (m *customCategoryReferenceModel) FindOne(ctx context.Context, id int64) (*CategoryReference, error) {
	return m.crud.FindOne(ctx, id)
}

func (m *customCategoryReferenceModel) Update(ctx context.Context, data *CategoryReference) error {
	return m.crud.Update(ctx, data.Id, data)
}

func (m *customCategoryReferenceModel) Delete(ctx context.Context, id int64) error {
	return m.crud.Delete(ctx, id)
}

package category

import (
	"context"

	"app/model"
	"gorm.io/gorm"
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

	customCategoryModel struct {
		crud *model.GormCrud[Category]
	}
)

// NewCategoryModel returns a model for the database table.
func NewCategoryModel(db *gorm.DB) CategoryModel {
	return &customCategoryModel{
		crud: model.NewGormCrud[Category](db, "category"),
	}
}

func (m *customCategoryModel) Insert(ctx context.Context, data *Category) error {
	return m.crud.Insert(ctx, data)
}

func (m *customCategoryModel) FindOne(ctx context.Context, id int64) (*Category, error) {
	return m.crud.FindOne(ctx, id)
}

func (m *customCategoryModel) Update(ctx context.Context, data *Category) error {
	return m.crud.Update(ctx, data.Id, data)
}

func (m *customCategoryModel) Delete(ctx context.Context, id int64) error {
	return m.crud.Delete(ctx, id)
}

func (m *customCategoryModel) SearchCategoryById(ctx context.Context, categoryID int64) (*Category, error) {
	return m.FindOne(ctx, categoryID)
}

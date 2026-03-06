package subCategory

import (
	"context"

	"app/model"
	"gorm.io/gorm"
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
		crud *model.GormCrud[SubCategory]
	}
)

// NewSubCategoryModel returns a model for the database table.
func NewSubCategoryModel(db *gorm.DB) SubCategoryModel {
	return &customSubCategoryModel{
		crud: model.NewGormCrud[SubCategory](db, "sub_category"),
	}
}

func (m *customSubCategoryModel) Insert(ctx context.Context, data *SubCategory) error {
	return m.crud.Insert(ctx, data)
}

func (m *customSubCategoryModel) FindOne(ctx context.Context, id int64) (*SubCategory, error) {
	return m.crud.FindOne(ctx, id)
}

func (m *customSubCategoryModel) Update(ctx context.Context, data *SubCategory) error {
	return m.crud.Update(ctx, data.Id, data)
}

func (m *customSubCategoryModel) Delete(ctx context.Context, id int64) error {
	return m.crud.Delete(ctx, id)
}

func (m *customSubCategoryModel) SearchSubCategoriesByIds(ctx context.Context, subCategoryIDs []int64) ([]SubCategory, error) {
	db, err := m.crud.Query(ctx)
	if err != nil {
		return nil, err
	}

	var items []SubCategory
	err = db.Where("id IN ?", subCategoryIDs).Find(&items).Error
	return items, err
}

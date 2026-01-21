package sync

import (
	"context"
	"gin_proj/common/exceptions"
	"gin_proj/config"
	"gin_proj/entity/po"

	"gorm.io/gorm"
)

type CategoryMapper struct{}

func (m *CategoryMapper) SearchSubCategoriesByIds(subCategoryIDs []int) []po.SubCategory {
	ctx := context.Background()
	subCategories, err := gorm.G[po.SubCategory](config.DB).Where("id IN ?", subCategoryIDs).Find(ctx)
	if err != nil {
		panic(exceptions.NewBusinessError("子分类查询错误", err.Error()))
	}
	return subCategories
}

func (m *CategoryMapper) SearchCategoryById(category_id int) po.Category {
	ctx := context.Background()
	category, err := gorm.G[po.Category](config.DB).Where("id = ?", category_id).First(ctx)
	if err != nil {
		panic(exceptions.NewBusinessError("分类查询错误", err.Error()))
	}
	return category
}

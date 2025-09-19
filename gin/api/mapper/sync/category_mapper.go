package sync

import (
	"gin_proj/config"
	"gin_proj/entity/po"
)

type CategoryMapper struct{}

func (m *CategoryMapper) SearchSubCategoriesByIds(subCategoryIDs []int) []po.SubCategory {
	var subCategories []po.SubCategory
	if err := config.DB.Where("id IN (?)", subCategoryIDs).Find(&subCategories).Error; err != nil {
		panic(err.Error())
	}
	return subCategories
}

func (m *CategoryMapper) SearchCategoryById(category_id int) po.Category {
	var category po.Category
	if err := config.DB.Where("id = ?", category_id).First(&category).Error; err != nil {
		panic(err.Error())
	}
	return category
}

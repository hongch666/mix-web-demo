package mapper

import (
	"gin_proj/config"
	"gin_proj/entity/po"
)

func SearchSubCategoriesByIds(subCategoryIDs []int) []po.SubCategory {
	var subCategories []po.SubCategory
	if err := config.DB.Where("id IN (?)", subCategoryIDs).Find(&subCategories).Error; err != nil {
		panic(err.Error())
	}
	return subCategories
}

func SearchCategoryById(category_id int) po.Category {
	var category po.Category
	if err := config.DB.Where("id = ?", category_id).First(&category).Error; err != nil {
		panic(err.Error())
	}
	return category
}

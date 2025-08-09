package mapper

import (
	"gin_proj/config"
	"gin_proj/entity/po"
)

func SearchArticles() []po.Article {
	var articles []po.Article
	if err := config.DB.Where("status = ?", 1).Find(&articles).Error; err != nil {
		panic(err.Error())
	}
	return articles
}

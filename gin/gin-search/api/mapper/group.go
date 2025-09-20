package mapper

import (
	"search/api/mapper/search"
	"search/api/mapper/sync"
)

type MapperGroup struct {
	ArticleMapper  sync.ArticleMapper
	CategoryMapper sync.CategoryMapper
	UserMapper     sync.UserMapper
	SearchMapper   search.SearchMapper
}

var Group = new(MapperGroup)

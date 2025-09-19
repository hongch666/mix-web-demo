package mapper

import (
	"gin_proj/api/mapper/chat"
	"gin_proj/api/mapper/search"
	"gin_proj/api/mapper/sync"
)

type MapperGroup struct {
	ArticleMapper     sync.ArticleMapper
	CategoryMapper    sync.CategoryMapper
	ChatMessageMapper chat.ChatMessageMapper
	UserMapper        sync.UserMapper
	SearchMapper      search.SearchMapper
}

var Group = new(MapperGroup)

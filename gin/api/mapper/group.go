package mapper

import (
	"gin_proj/api/mapper/chat"
	"gin_proj/api/mapper/search"
	"gin_proj/api/mapper/sync"
)

type MapperGroup struct {
	ArticleMapper     sync.ArticleMapper
	CategoryMapper    sync.CategoryMapper
	UserMapper        sync.UserMapper
	CommentMapper     sync.CommentMapper
	LikeMapper        sync.LikeMapper
	CollectMapper     sync.CollectMapper
	ChatMessageMapper chat.ChatMessageMapper
	SearchMapper      search.SearchMapper
}

var Group = new(MapperGroup)

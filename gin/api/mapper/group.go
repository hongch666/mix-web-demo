package mapper

import (
	"github.com/hongch666/mix-web-demo/gin/api/mapper/chat"
	"github.com/hongch666/mix-web-demo/gin/api/mapper/search"
	"github.com/hongch666/mix-web-demo/gin/api/mapper/sync"
)

type MapperGroup struct {
	ArticleMapper     sync.ArticleMapper
	CategoryMapper    sync.CategoryMapper
	UserMapper        sync.UserMapper
	CommentMapper     sync.CommentMapper
	LikeMapper        sync.LikeMapper
	CollectMapper     sync.CollectMapper
	FocusMapper       sync.FocusMapper
	ChatMessageMapper chat.ChatMessageMapper
	SearchMapper      search.SearchMapper
}

var Group = new(MapperGroup)

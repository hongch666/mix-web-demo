package mapper

type MapperGroup struct {
	ArticleMapper     ArticleMapper
	CategoryMapper    CategoryMapper
	ChatMessageMapper ChatMessageMapper
	UserMapper        UserMapper
	SearchMapper      SearchMapper
}

var Group = new(MapperGroup)

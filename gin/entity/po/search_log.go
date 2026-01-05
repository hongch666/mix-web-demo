package po

import "time"

// SearchLog MongoDB 中的搜索日志实体
type SearchLog struct {
	ID        string         `bson:"_id,omitempty"`
	UserID    int64          `bson:"userId"`
	ArticleID *int64         `bson:"articleId,omitempty"`
	Action    string         `bson:"action"`
	Content   map[string]any `bson:"content"`
	Msg       string         `bson:"msg"`
	CreatedAt time.Time      `bson:"createdAt"`
	UpdatedAt time.Time      `bson:"updatedAt"`
}

// SearchContent 解析 Content 字段中的搜索内容
type SearchContent struct {
	Keyword         string  `json:"Keyword"`
	UserID          *int64  `json:"UserID"`
	Username        string  `json:"Username"`
	CategoryName    string  `json:"CategoryName"`
	SubCategoryName string  `json:"SubCategoryName"`
	StartDate       *string `json:"StartDate"`
	EndDate         *string `json:"EndDate"`
	Page            int     `json:"Page"`
	Size            int     `json:"Size"`
}

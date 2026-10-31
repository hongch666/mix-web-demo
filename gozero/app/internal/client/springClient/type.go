package springClient

import (
	"context"

	"app/common/client"
)

// Client 定义 GoZero 使用的 Spring 调用契约，便于业务层隔离远程依赖
type Client interface {
	GetPublishedArticles(context.Context, int, int) (client.Result, error)
	FetchArticleStats(context.Context, []int64, []int64) (ArticleStats, error)
	GetArticlesByIDs(context.Context, []int64) (client.Result, error)
	IsAdminUser(context.Context, int64) (bool, error)
	GetUsersByIDs(context.Context, []int64) (client.Result, error)
	GetCategoriesByIDs(context.Context, []int64) (client.Result, error)
	GetSubCategoriesByIDs(context.Context, []int64) (client.Result, error)
}

// ArticleVO 文章视图对象
type ArticleVO struct {
	ID              int64  `json:"id"`
	Title           string `json:"title"`
	Content         string `json:"content"`
	UserID          int64  `json:"user_id"`
	Username        string `json:"username"`
	Tags            string `json:"tags"`
	Status          int    `json:"status"`
	Views           int    `json:"views"`
	SubCategoryID   int    `json:"sub_category_id"`
	SubCategoryName string `json:"sub_category_name"`
	CategoryID      int64  `json:"category_id"`
	CategoryName    string `json:"category_name"`
	CreateAt        string `json:"create_at"`
	UpdateAt        string `json:"update_at"`
}

// UserVO 用户视图对象
type UserVO struct {
	ID    int64  `json:"id"`
	Name  string `json:"name"`
	Role  string `json:"role"`
	Img   string `json:"img"`
	Email string `json:"email"`
}

// CommentScoreVO 评论评分
type CommentScoreVO struct {
	AverageScore float64 `json:"average_score"`
	Count        int64   `json:"count"`
}

// IdCountVO Spring 批量统计返回的元素，字段与 Spring 的 IdCountVO 保持一致
type IdCountVO struct {
	ID    int64 `json:"id"`
	Count int64 `json:"count"`
}

// ArticleCommentScoresVO Spring 评论评分返回的元素，按角色分组
type ArticleCommentScoresVO struct {
	ArticleID  int64                     `json:"article_id"`
	RoleScores map[string]CommentScoreVO `json:"role_scores"`
}

// ArticleStatsBatchVO Spring 合并统计接口的返回体，字段与 Spring 的 ArticleStatsBatchVO 保持一致
type ArticleStatsBatchVO struct {
	Views         []IdCountVO              `json:"views"`
	Likes         []IdCountVO              `json:"likes"`
	Collects      []IdCountVO              `json:"collects"`
	Follows       []IdCountVO              `json:"follows"`
	CommentScores []ArticleCommentScoresVO `json:"comment_scores"`
}

// CategoryVO 分类视图对象
type CategoryVO struct {
	ID   int64  `json:"id"`
	Name string `json:"name"`
}

// SubCategoryVO 子分类视图对象
type SubCategoryVO struct {
	ID         int64  `json:"id"`
	Name       string `json:"name"`
	CategoryID int64  `json:"category_id"`
}

// PageVO 分页视图对象
type PageVO[T any] struct {
	Total   int64 `json:"total"`
	Records []T   `json:"list"`
}

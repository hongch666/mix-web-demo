package po

type ArticleES struct {
	ID               int     `json:"id"`
	Title            string  `json:"title"`
	Content          string  `json:"content"`
	UserID           int     `json:"userId"`
	Username         string  `json:"username"`
	Tags             string  `json:"tags"`
	Status           int     `json:"status"`
	Views            int     `json:"views"`
	CategoryName     string  `json:"category_name"`
	SubCategoryName  string  `json:"sub_category_name"`
	CreateAt         string  `json:"create_at"`
	UpdateAt         string  `json:"update_at"`
	AIScore          float64 `json:"ai_score"`           // AI评分平均值（1-5）
	UserScore        float64 `json:"user_score"`         // 用户评分平均值（1-5）
	AICommentCount   int     `json:"ai_comment_count"`   // AI评论数
	UserCommentCount int     `json:"user_comment_count"` // 用户评论数
}

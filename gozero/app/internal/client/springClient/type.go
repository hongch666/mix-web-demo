package springClient

// TestResponse Spring 服务测试响应
type TestResponse struct {
	Data string `json:"data"`
}

type ArticleSearchDoc struct {
	ID                int64   `json:"id"`
	Title             string  `json:"title"`
	Content           string  `json:"content"`
	UserID            int64   `json:"userId"`
	Username          string  `json:"username"`
	Tags              string  `json:"tags"`
	Status            int     `json:"status"`
	Views             int     `json:"views"`
	LikeCount         int     `json:"likeCount"`
	CollectCount      int     `json:"collectCount"`
	AuthorFollowCount int     `json:"authorFollowCount"`
	CategoryName      string  `json:"category_name"`
	SubCategoryName   string  `json:"sub_category_name"`
	CreateAt          string  `json:"create_at"`
	UpdateAt          string  `json:"update_at"`
	AIScore           float64 `json:"ai_score"`
	UserScore         float64 `json:"user_score"`
	AICommentCount    int     `json:"ai_comment_count"`
	UserCommentCount  int     `json:"user_comment_count"`
}

type ArticleSearchDocsPage struct {
	NextCursor int64              `json:"nextCursor"`
	HasMore    bool               `json:"hasMore"`
	List       []ArticleSearchDoc `json:"list"`
}

type ArticleStatistic struct {
	ArticleID         int64 `json:"articleId"`
	Views             int   `json:"views"`
	LikeCount         int   `json:"likeCount"`
	CollectCount      int   `json:"collectCount"`
	AuthorFollowCount int   `json:"authorFollowCount"`
}

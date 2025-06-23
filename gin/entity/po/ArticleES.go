package po

type ArticleES struct {
	ID       int    `json:"id"`
	Title    string `json:"title"`
	Content  string `json:"content"`
	UserID   int    `json:"userId"`
	Username string `json:"username"`
	Tags     string `json:"tags"`
	Status   int    `json:"status"`
	Views    int    `json:"views"`
	CreateAt string `json:"create_at"`
	UpdateAt string `json:"update_at"`
}

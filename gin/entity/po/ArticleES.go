package po

type ArticleES struct {
	ID              int    `json:"id"`
	Title           string `json:"title"`
	Content         string `json:"content"`
	UserID          int    `json:"userId"`
	Username        string `json:"username"`
	Tags            string `json:"tags"`
	Status          int    `json:"status"`
	Views           int    `json:"views"`
	CategoryName    string `json:"category_name"`
	SubCategoryName string `json:"sub_category_name"`
	CreateAt        string `json:"create_at"`
	UpdateAt        string `json:"update_at"`
}

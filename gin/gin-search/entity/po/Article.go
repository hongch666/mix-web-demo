package po

type Article struct {
	ID            uint   `gorm:"primaryKey" json:"id"`
	Title         string `json:"title"`
	Content       string `json:"content"`
	UserID        uint   `json:"userId"`
	Tags          string `json:"tags"`
	Status        int    `json:"status"`        // 1 表示已发布
	Views         int    `json:"views"`         // 浏览量
	SubCategoryID int    `json:"subCategoryId"` // 子分类ID
	CreateAt      string `json:"createAt"`
	UpdateAt      string `json:"updateAt"`
}

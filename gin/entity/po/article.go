package po

import "time"

type Article struct {
	ID            uint      `gorm:"column:id" json:"id"`
	Title         string    `gorm:"column:title" json:"title"`
	Content       string    `gorm:"column:content" json:"content"`
	UserID        uint      `gorm:"column:user_id" json:"userId"`
	SubCategoryID int       `gorm:"column:sub_category_id" json:"sub_category_id"`
	Tags          string    `gorm:"column:tags" json:"tags"`
	Status        int       `gorm:"column:status" json:"status"` // 1 表示已发布
	Views         int       `gorm:"column:views" json:"views"`   // 浏览量
	CreateAt      time.Time `gorm:"column:create_at" json:"createdAt"`
	UpdateAt      time.Time `gorm:"column:update_at" json:"updatedAt"`
}

func (Article) TableName() string {
	return "articles"
}

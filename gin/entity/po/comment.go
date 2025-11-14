package po

import "time"

type Comment struct {
	ID         int       `gorm:"column:id" json:"id"`
	ArticleID  int       `gorm:"column:article_id" json:"article_id"`
	UserID     int       `gorm:"column:user_id" json:"user_id"`
	Content    string    `gorm:"column:content" json:"content"`
	Star       float64   `gorm:"column:star" json:"star"`
	CreateTime time.Time `gorm:"column:create_time" json:"create_time"`
	UpdateTime time.Time `gorm:"column:update_time" json:"update_time"`
}

func (Comment) TableName() string {
	return "comments"
}

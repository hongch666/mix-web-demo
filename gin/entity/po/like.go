package po

import "time"

type Like struct {
	ID        uint      `gorm:"column:id" json:"id"`
	ArticleID uint      `gorm:"column:article_id" json:"articleId"`
	UserID    uint      `gorm:"column:user_id" json:"userId"`
	CreatedAt time.Time `gorm:"column:created_time" json:"createdAt"`
}

func (Like) TableName() string {
	return "likes"
}

package po

import "time"

type Like struct {
	ID        uint      `gorm:"primaryKey" json:"id"`
	ArticleID uint      `json:"articleId"`
	UserID    uint      `json:"userId"`
	CreatedAt time.Time `json:"createdAt"`
}

func (Like) TableName() string {
	return "likes"
}

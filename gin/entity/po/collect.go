package po

import "time"

type Collect struct {
	ID        uint      `gorm:"primaryKey" json:"id"`
	ArticleID uint      `json:"articleId"`
	UserID    uint      `json:"userId"`
	CreatedAt time.Time `json:"createdAt"`
}

func (Collect) TableName() string {
	return "collects"
}

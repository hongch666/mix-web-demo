package po

import "time"

type Article struct {
	ID        uint      `gorm:"primaryKey" json:"id"`
	Title     string    `json:"title"`
	Content   string    `json:"content"`
	UserID    uint      `json:"userId"`
	Tags      string    `json:"tags"`
	Status    int       `json:"status"` // 1 表示已发布
	CreatedAt time.Time `json:"createdAt"`
	UpdatedAt time.Time `json:"updatedAt"`
}

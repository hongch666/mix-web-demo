package po

import "time"

type ArticleES struct {
	ID        uint      `json:"id"`
	Title     string    `json:"title"`
	Content   string    `json:"content"`
	UserID    uint      `json:"userId"`
	Tags      string    `json:"tags"`
	Status    int       `json:"status"`
	Views     int       `json:"views"`
	CreatedAt time.Time `json:"createdAt"`
	UpdatedAt time.Time `json:"updatedAt"`
}

package po

import "time"

type ChatMessage struct {
	ID         uint      `gorm:"column:id" json:"id"`
	SenderID   string    `gorm:"column:sender_id" json:"senderId"`
	ReceiverID string    `gorm:"column:receiver_id" json:"receiverId"`
	Content    string    `gorm:"column:content" json:"content"`
	IsRead     int8      `gorm:"column:is_read" json:"isRead"`
	CreatedAt  time.Time `gorm:"column:created_at" json:"createdAt"`
}

func (ChatMessage) TableName() string {
	return "chat_messages"
}

package po

import "time"

type ChatMessage struct {
	ID         uint      `json:"id" gorm:"primaryKey;autoIncrement"`
	SenderID   string    `json:"senderId" gorm:"column:sender_id;type:varchar(50);not null;index"`
	ReceiverID string    `json:"receiverId" gorm:"column:receiver_id;type:varchar(50);not null;index"`
	Content    string    `json:"content" gorm:"type:text;not null"`
	CreatedAt  time.Time `json:"createdAt" gorm:"autoCreateTime"`
}

func (ChatMessage) TableName() string {
	return "chat_messages"
}

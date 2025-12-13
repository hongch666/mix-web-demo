package po

import "time"

type ChatMessage struct {
	ID         uint      `json:"id" gorm:"primaryKey;autoIncrement"`
	SenderID   string    `json:"senderId" gorm:"column:sender_id;type:varchar(50);not null;index"`
	ReceiverID string    `json:"receiverId" gorm:"column:receiver_id;type:varchar(50);not null;index"`
	Content    string    `json:"content" gorm:"type:text;not null"`
	IsRead     int8      `json:"isRead" gorm:"column:is_read;type:tinyint;default:0;not null;comment:是否已读，0为未读，1为已读"` // 0: unread, 1: read
	CreatedAt  time.Time `json:"createdAt" gorm:"autoCreateTime"`
}

func (ChatMessage) TableName() string {
	return "chat_messages"
}

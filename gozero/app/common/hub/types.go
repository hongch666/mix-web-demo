package hub

type ChatMessageItem struct {
	ID         uint   `json:"id"`
	SenderID   string `json:"sender_id"`
	ReceiverID string `json:"receiver_id"`
	Content    string `json:"content"`
	IsRead     int8   `json:"is_read"`
	CreatedAt  string `json:"created_at"`
}

type WebSocketMessage struct {
	Type       string `json:"type"` // message, ping, pong
	SenderID   string `json:"sender_id,omitempty"`
	ReceiverID string `json:"receiver_id,omitempty"`
	Content    string `json:"content,omitempty"`
	MessageID  uint   `json:"message_id,omitempty"`
	Timestamp  string `json:"timestamp,omitempty"`
}

// SSE消息格式
type SSEMessageNotification struct {
	Type         string           `json:"type"` // "message"
	UserID       string           `json:"user_id"`
	UnreadCounts map[string]int64 `json:"unread_counts"` // key: otherUserId, value: unreadCount
	Message      *ChatMessageItem `json:"message,omitempty"`
}

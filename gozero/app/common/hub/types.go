package hub

type ChatMessageItem struct {
	ID         uint   `json:"id"`
	SenderID   string `json:"senderId"`
	ReceiverID string `json:"receiverId"`
	Content    string `json:"content"`
	IsRead     int8   `json:"isRead"`
	CreatedAt  string `json:"createdAt"`
}

type WebSocketMessage struct {
	Type       string `json:"type"` // message, ping, pong
	SenderID   string `json:"senderId,omitempty"`
	ReceiverID string `json:"receiverId,omitempty"`
	Content    string `json:"content,omitempty"`
	MessageID  uint   `json:"messageId,omitempty"`
	Timestamp  string `json:"timestamp,omitempty"`
}

// SSE消息格式
type SSEMessageNotification struct {
	Type         string           `json:"type"` // "message"
	UserID       string           `json:"userId"`
	UnreadCounts map[string]int64 `json:"unreadCounts"` // key: otherUserId, value: unreadCount
	Message      *ChatMessageItem `json:"message,omitempty"`
}
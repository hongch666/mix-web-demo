package hub

type ChatMessageItem struct {
	ID         uint   `json:"id"`
	SenderID   int64  `json:"sender_id"`
	ReceiverID int64  `json:"receiver_id"`
	Content    string `json:"content"`
	IsRead     int8   `json:"is_read"`
	CreatedAt  string `json:"created_at"`
}

type WebSocketMessage struct {
	Type       string `json:"type"` // message, ping, pong
	SenderID   int64  `json:"sender_id,omitempty"`
	ReceiverID int64  `json:"receiver_id,omitempty"`
	Content    string `json:"content,omitempty"`
	MessageID  uint   `json:"message_id,omitempty"`
	Timestamp  string `json:"timestamp,omitempty"`
}

// SSE消息格式
type SSEMessageNotification struct {
	Type         string           `json:"type"` // "message"
	UserID       int64            `json:"user_id"`
	UnreadCounts map[int64]int64  `json:"unread_counts"` // key: otherUserId, value: unreadCount
	Message      *ChatMessageItem `json:"message,omitempty"`
}

// ChatRealtimeEvent 跨 Pod 传递的聊天实时事件
type ChatRealtimeEvent struct {
	Type             string                  `json:"type"`
	ReceiverID       int64                   `json:"receiver_id"`
	WebSocketMessage *WebSocketMessage       `json:"websocket_message,omitempty"`
	SSENotification  *SSEMessageNotification `json:"sse_notification,omitempty"`
}

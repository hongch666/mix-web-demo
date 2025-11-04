package dto

type SendMessageRequest struct {
	SenderID   string `json:"senderId" binding:"required"`
	ReceiverID string `json:"receiverId" binding:"required"`
	Content    string `json:"content" binding:"required"`
}

type SendMessageResponse struct {
	MessageID uint `json:"messageId"`
}

type GetChatHistoryRequest struct {
	UserID  string `json:"userId" binding:"required"`
	OtherID string `json:"otherId" binding:"required"`
	Page    int    `json:"page"`
	Size    int    `json:"size"`
}

type GetChatHistoryResponse struct {
	Messages []ChatMessageItem `json:"messages"`
	Total    int64             `json:"total"`
}

type ChatMessageItem struct {
	ID         uint   `json:"id"`
	SenderID   string `json:"senderId"`
	ReceiverID string `json:"receiverId"`
	Content    string `json:"content"`
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

type QueueStatusResponse struct {
	OnlineUsers []string `json:"onlineUsers"`
	Count       int      `json:"count"`
}

type JoinQueueRequest struct {
	UserID string `json:"userId" binding:"required"`
}

type JoinQueueResponse struct {
	UserID string `json:"userId"`
	Status string `json:"status"` // joined, already_in_queue
}

type LeaveQueueRequest struct {
	UserID string `json:"userId" binding:"required"`
}

type LeaveQueueResponse struct {
	UserID string `json:"userId"`
	Status string `json:"status"` // left, not_in_queue
}

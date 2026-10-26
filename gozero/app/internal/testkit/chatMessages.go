package testkit

import (
	"context"
	"time"

	"app/model/chatMessages"
)

// ChatMessageModelFake 聊天消息模型的内存替身，用字段注入查询结果与错误，并记录调用参数供断言
type ChatMessageModelFake struct {
	chatMessages.ChatMessagesModel
	Created   *chatMessages.ChatMessages
	CreateErr error
	Unread    map[int64]int64
	UnreadErr error
	Messages  []*chatMessages.ChatMessages
	Total     int64
	// HistoryErr 模拟历史查询失败，MarkErr 模拟标记已读失败
	HistoryErr error
	MarkErr    error

	HistoryOffset int
	HistoryLimit  int
	MarkCalled    bool

	SingleUnread  int64
	SingleErr     error
	SingleUserID  int64
	SingleOtherID int64
}

// CreateChatMessage 记录待保存的消息，成功时回填固定主键与创建时间
func (m *ChatMessageModelFake) CreateChatMessage(_ context.Context, message *chatMessages.ChatMessages) error {
	m.Created = message
	if m.CreateErr == nil {
		message.Id = 42
		message.CreatedAt = time.Date(2026, 1, 2, 3, 4, 5, 0, time.UTC)
	}
	return m.CreateErr
}

// GetAllUnreadCounts 返回预置的未读映射或错误
func (m *ChatMessageModelFake) GetAllUnreadCounts(_ context.Context, _ int64) (map[int64]int64, error) {
	return m.Unread, m.UnreadErr
}

// GetUnreadCount 记录查询的两个用户并返回预置未读数或错误
func (m *ChatMessageModelFake) GetUnreadCount(_ context.Context, userID, otherID int64) (int64, error) {
	m.SingleUserID, m.SingleOtherID = userID, otherID
	return m.SingleUnread, m.SingleErr
}

// GetChatHistory 记录分页参数并返回预置消息列表、总数或错误
func (m *ChatMessageModelFake) GetChatHistory(_ context.Context, _, _ int64, offset, limit int) ([]*chatMessages.ChatMessages, int64, error) {
	m.HistoryOffset, m.HistoryLimit = offset, limit
	return m.Messages, m.Total, m.HistoryErr
}

// MarkChatHistoryAsRead 标记调用发生并返回预置错误
func (m *ChatMessageModelFake) MarkChatHistoryAsRead(_ context.Context, _, _ int64) error {
	m.MarkCalled = true
	return m.MarkErr
}

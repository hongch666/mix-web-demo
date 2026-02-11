package chat

import (
	"context"

	"github.com/hongch666/mix-web-demo/gin/common/config"
	"github.com/hongch666/mix-web-demo/gin/common/exceptions"
	"github.com/hongch666/mix-web-demo/gin/common/utils"
	"github.com/hongch666/mix-web-demo/gin/entity/po"

	"gorm.io/gorm"
)

type ChatMessageMapper struct{}

func (m *ChatMessageMapper) CreateChatMessage(message *po.ChatMessage) {
	ctx := context.Background()
	if err := gorm.G[po.ChatMessage](config.DB).Create(ctx, message); err != nil {
		panic(exceptions.NewBusinessError(utils.CREATE_MESSAGE_ERROR, err.Error()))
	}
}

func (m *ChatMessageMapper) GetChatHistory(userID, otherID string, offset, limit int) ([]*po.ChatMessage, int64) {
	// 计算总数
	ctx := context.Background()
	total, err := gorm.G[po.ChatMessage](config.DB).Where(
		"(sender_id = ? AND receiver_id = ?) OR (sender_id = ? AND receiver_id = ?)",
		userID, otherID, otherID, userID,
	).Count(ctx, "*")
	if err != nil {
		panic(exceptions.NewBusinessError(utils.GET_HISTORY_MESSAGE_ERROR, err.Error()))
	}

	// 分页查询，按创建时间升序排列
	messages, err := gorm.G[po.ChatMessage](config.DB).Where(
		"(sender_id = ? AND receiver_id = ?) OR (sender_id = ? AND receiver_id = ?)",
		userID, otherID, otherID, userID,
	).Order("created_at ASC").Offset(offset).Limit(limit).Find(ctx)
	if err != nil {
		panic(exceptions.NewBusinessError(utils.GET_HISTORY_MESSAGE_ERROR, err.Error()))
	}

	// 转换为指针切片
	var result []*po.ChatMessage
	for i := range messages {
		result = append(result, &messages[i])
	}

	return result, total
}

// GetUnreadCount 获取两个用户间的未读消息数
func (m *ChatMessageMapper) GetUnreadCount(userID, otherID string) int64 {
	ctx := context.Background()
	count, err := gorm.G[po.ChatMessage](config.DB).Where(
		"receiver_id = ? AND sender_id = ? AND is_read = 0",
		userID, otherID,
	).Count(ctx, "*")
	if err != nil {
		panic(exceptions.NewBusinessError(utils.GET_UNREAD_COUNT_ERROR, err.Error()))
	}
	return count
}

// GetAllUnreadCounts 获取用户与其他所有人的未读消息数
func (m *ChatMessageMapper) GetAllUnreadCounts(userID string) map[string]int64 {
	ctx := context.Background()

	// 获取所有发给当前用户的未读消息，按发送者分组统计
	var results []struct {
		SenderID string
		Count    int64
	}

	err := config.DB.WithContext(ctx).
		Model(&po.ChatMessage{}).
		Select("sender_id, COUNT(*) as count").
		Where("receiver_id = ? AND is_read = 0", userID).
		Group("sender_id").
		Scan(&results).
		Error

	if err != nil {
		panic(exceptions.NewBusinessError(utils.GET_ALL_UNREAD_COUNTS_ERROR, err.Error()))
	}

	unreadCounts := make(map[string]int64)
	for _, result := range results {
		unreadCounts[result.SenderID] = result.Count
	}

	return unreadCounts
}

// MarkAsRead 将指定消息标记为已读
func (m *ChatMessageMapper) MarkAsRead(messageID uint) error {
	ctx := context.Background()
	return config.DB.WithContext(ctx).
		Model(&po.ChatMessage{}).
		Where("id = ?", messageID).
		Update("is_read", 1).
		Error
}

// MarkChatHistoryAsRead 将两个用户间的所有消息标记为已读
func (m *ChatMessageMapper) MarkChatHistoryAsRead(userID, otherID string) error {
	ctx := context.Background()
	return config.DB.WithContext(ctx).
		Model(&po.ChatMessage{}).
		Where("receiver_id = ? AND sender_id = ?", userID, otherID).
		Update("is_read", 1).
		Error
}

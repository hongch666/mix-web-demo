package chat

import (
	"chat/config"
	"chat/entity/po"
	"context"

	"gorm.io/gorm"
)

type ChatMessageMapper struct{}

func (m *ChatMessageMapper) CreateChatMessage(message *po.ChatMessage) {
	ctx := context.Background()
	if err := gorm.G[po.ChatMessage](config.DB).Create(ctx, message); err != nil {
		panic(err)
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
		panic(err)
	}

	// 分页查询，按创建时间升序排列
	messages, err := gorm.G[po.ChatMessage](config.DB).Where(
		"(sender_id = ? AND receiver_id = ?) OR (sender_id = ? AND receiver_id = ?)",
		userID, otherID, otherID, userID,
	).Order("created_at ASC").Offset(offset).Limit(limit).Find(ctx)
	if err != nil {
		panic(err)
	}

	// 转换为指针切片
	var result []*po.ChatMessage
	for i := range messages {
		result = append(result, &messages[i])
	}

	return result, total
}

package mapper

import (
	"gin_proj/entity/po"

	"gorm.io/gorm"
)

type ChatMessageMapper struct {
	db *gorm.DB
}

func NewChatMessageMapper(db *gorm.DB) *ChatMessageMapper {
	return &ChatMessageMapper{db: db}
}

func (m *ChatMessageMapper) CreateMessage(message *po.ChatMessage) error {
	return m.db.Create(message).Error
}

func (m *ChatMessageMapper) GetChatHistory(userID, otherID string, offset, limit int) ([]*po.ChatMessage, int64, error) {
	var messages []*po.ChatMessage
	var total int64

	// 查询两个用户之间的所有聊天记录
	query := m.db.Model(&po.ChatMessage{}).Where(
		"(sender_id = ? AND receiver_id = ?) OR (sender_id = ? AND receiver_id = ?)",
		userID, otherID, otherID, userID,
	)

	// 计算总数
	if err := query.Count(&total).Error; err != nil {
		return nil, 0, err
	}

	// 分页查询，按创建时间升序排列
	if err := query.Order("created_at ASC").Offset(offset).Limit(limit).Find(&messages).Error; err != nil {
		return nil, 0, err
	}

	return messages, total, nil
}

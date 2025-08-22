package mapper

import (
	"gin_proj/config"
	"gin_proj/entity/po"
)

func CreateChatMessage(message *po.ChatMessage) {
	// GORM Create 返回 *gorm.DB，需要检查返回值的 Error 字段
	result := config.DB.Create(message)
	if result.Error != nil {
		panic(result.Error)
	}
}

func GetChatHistory(userID, otherID string, offset, limit int) ([]*po.ChatMessage, int64) {
	var messages []*po.ChatMessage
	var total int64

	// 查询两个用户之间的所有聊天记录
	query := config.DB.Model(&po.ChatMessage{}).Where(
		"(sender_id = ? AND receiver_id = ?) OR (sender_id = ? AND receiver_id = ?)",
		userID, otherID, otherID, userID,
	)

	// 计算总数
	if err := query.Count(&total).Error; err != nil {
		panic(err)
	}

	// 分页查询，按创建时间升序排列
	if err := query.Order("created_at ASC").Offset(offset).Limit(limit).Find(&messages).Error; err != nil {
		panic(err)
	}

	return messages, total
}

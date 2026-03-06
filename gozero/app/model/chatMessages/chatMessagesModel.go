package chatMessages

import (
	"context"

	"app/model"
	"gorm.io/gorm"
)

var _ ChatMessagesModel = (*customChatMessagesModel)(nil)

type (
	ChatMessagesModel interface {
		Insert(ctx context.Context, data *ChatMessages) error
		FindOne(ctx context.Context, id uint64) (*ChatMessages, error)
		Update(ctx context.Context, data *ChatMessages) error
		Delete(ctx context.Context, id uint64) error
		CreateChatMessage(ctx context.Context, message *ChatMessages) error
		GetChatHistory(ctx context.Context, userID, otherID string, offset, limit int) ([]*ChatMessages, int64, error)
		GetUnreadCount(ctx context.Context, userID, otherID string) (int64, error)
		GetAllUnreadCounts(ctx context.Context, userID string) (map[string]int64, error)
		MarkAsRead(ctx context.Context, messageID uint64) error
		MarkChatHistoryAsRead(ctx context.Context, userID, otherID string) error
	}

	customChatMessagesModel struct {
		crud *model.GormCrud[ChatMessages]
	}
)

// NewChatMessagesModel returns a model for the database table.
func NewChatMessagesModel(db *gorm.DB) ChatMessagesModel {
	return &customChatMessagesModel{
		crud: model.NewGormCrud[ChatMessages](db, "chat_messages"),
	}
}

func (m *customChatMessagesModel) Insert(ctx context.Context, data *ChatMessages) error {
	return m.crud.Insert(ctx, data)
}

func (m *customChatMessagesModel) FindOne(ctx context.Context, id uint64) (*ChatMessages, error) {
	return m.crud.FindOne(ctx, id)
}

func (m *customChatMessagesModel) Update(ctx context.Context, data *ChatMessages) error {
	return m.crud.Update(ctx, data.Id, data)
}

func (m *customChatMessagesModel) Delete(ctx context.Context, id uint64) error {
	return m.crud.Delete(ctx, id)
}

func (m *customChatMessagesModel) CreateChatMessage(ctx context.Context, message *ChatMessages) error {
	return m.Insert(ctx, message)
}

func (m *customChatMessagesModel) GetChatHistory(ctx context.Context, userID, otherID string, offset, limit int) ([]*ChatMessages, int64, error) {
	db, err := m.crud.Query(ctx)
	if err != nil {
		return nil, 0, err
	}

	query := db.Where("(sender_id = ? AND receiver_id = ?) OR (sender_id = ? AND receiver_id = ?)", userID, otherID, otherID, userID)

	var total int64
	if err := query.Count(&total).Error; err != nil {
		return nil, 0, err
	}

	var messages []ChatMessages
	if err := query.Order("created_at ASC").Offset(offset).Limit(limit).Find(&messages).Error; err != nil {
		return nil, 0, err
	}

	result := make([]*ChatMessages, 0, len(messages))
	for i := range messages {
		result = append(result, &messages[i])
	}

	return result, total, nil
}

func (m *customChatMessagesModel) GetUnreadCount(ctx context.Context, userID, otherID string) (int64, error) {
	db, err := m.crud.Query(ctx)
	if err != nil {
		return 0, err
	}

	var count int64
	err = db.Where("receiver_id = ? AND sender_id = ? AND is_read = 0", userID, otherID).Count(&count).Error
	return count, err
}

func (m *customChatMessagesModel) GetAllUnreadCounts(ctx context.Context, userID string) (map[string]int64, error) {
	db, err := m.crud.Query(ctx)
	if err != nil {
		return nil, err
	}

	var rows []struct {
		SenderID string `gorm:"column:sender_id"`
		Count    int64  `gorm:"column:count"`
	}
	err = db.Select("sender_id, COUNT(*) as count").Where("receiver_id = ? AND is_read = 0", userID).Group("sender_id").Scan(&rows).Error
	if err != nil {
		return nil, err
	}

	result := make(map[string]int64)
	for _, row := range rows {
		result[row.SenderID] = row.Count
	}

	return result, nil
}

func (m *customChatMessagesModel) MarkAsRead(ctx context.Context, messageID uint64) error {
	db, err := m.crud.Query(ctx)
	if err != nil {
		return err
	}
	return db.Where("id = ?", messageID).Update("is_read", 1).Error
}

func (m *customChatMessagesModel) MarkChatHistoryAsRead(ctx context.Context, userID, otherID string) error {
	db, err := m.crud.Query(ctx)
	if err != nil {
		return err
	}
	return db.Where("receiver_id = ? AND sender_id = ?", userID, otherID).Update("is_read", 1).Error
}

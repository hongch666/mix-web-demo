package chatMessages

import (
	"context"
	"fmt"

	"github.com/zeromicro/go-zero/core/stores/sqlx"
)

var _ ChatMessagesModel = (*customChatMessagesModel)(nil)

type (
	ChatMessagesModel interface {
		Insert(context.Context, *ChatMessages) error
		FindOne(context.Context, uint64) (*ChatMessages, error)
		Update(context.Context, *ChatMessages) error
		Delete(context.Context, uint64) error
		CreateChatMessage(context.Context, *ChatMessages) error
		GetChatHistory(context.Context, int64, int64, int, int) ([]*ChatMessages, int64, error)
		GetUnreadCount(context.Context, int64, int64) (int64, error)
		GetAllUnreadCounts(context.Context, int64) (map[int64]int64, error)
		MarkAsRead(context.Context, uint64) error
		MarkChatHistoryAsRead(context.Context, int64, int64) error
	}
	customChatMessagesModel struct {
		conn      sqlx.SqlConn
		baseModel *defaultChatMessagesModel
	}
)

func NewChatMessagesModel(conn sqlx.SqlConn) ChatMessagesModel {
	return &customChatMessagesModel{conn: conn, baseModel: newChatMessagesModel(conn)}
}

func (m *customChatMessagesModel) Insert(ctx context.Context, data *ChatMessages) error {
	_, err := m.baseModel.Insert(ctx, data)
	return err
}

func (m *customChatMessagesModel) FindOne(ctx context.Context, id uint64) (*ChatMessages, error) {
	return m.baseModel.FindOne(ctx, id)
}

func (m *customChatMessagesModel) Update(ctx context.Context, data *ChatMessages) error {
	return m.baseModel.Update(ctx, data)
}

func (m *customChatMessagesModel) Delete(ctx context.Context, id uint64) error {
	return m.baseModel.Delete(ctx, id)
}

func (m *customChatMessagesModel) CreateChatMessage(ctx context.Context, message *ChatMessages) error {
	result, err := m.baseModel.Insert(ctx, message)
	if err != nil {
		return err
	}
	// 回填自增主键，用于后续查询完整记录
	id, err := result.LastInsertId()
	if err != nil {
		return err
	}
	created, err := m.FindOne(ctx, uint64(id))
	if err != nil {
		return err
	}
	// 将数据库生成的字段（id、created_at 等）回写到入参对象，避免调用方拿到零值
	*message = *created
	return nil
}

func (m *customChatMessagesModel) GetChatHistory(ctx context.Context, userID, otherID int64, offset, limit int) ([]*ChatMessages, int64, error) {
	var total int64
	where := "(sender_id = ? and receiver_id = ?) or (sender_id = ? and receiver_id = ?)"
	countQuery := fmt.Sprintf("select count(*) from %s where %s", m.baseModel.table, where)
	if err := m.conn.QueryRowCtx(ctx, &total, countQuery, userID, otherID, otherID, userID); err != nil {
		return nil, 0, err
	}
	var messages []ChatMessages
	dataQuery := fmt.Sprintf("select %s from %s where %s order by created_at asc limit ? offset ?", chatMessagesRows, m.baseModel.table, where)
	if err := m.conn.QueryRowsCtx(ctx, &messages, dataQuery, userID, otherID, otherID, userID, limit, offset); err != nil {
		return nil, 0, err
	}
	result := make([]*ChatMessages, 0, len(messages))
	for i := range messages {
		result = append(result, &messages[i])
	}
	return result, total, nil
}

func (m *customChatMessagesModel) GetUnreadCount(ctx context.Context, userID, otherID int64) (int64, error) {
	var count int64
	err := m.conn.QueryRowCtx(ctx, &count, fmt.Sprintf("select count(*) from %s where receiver_id = ? and sender_id = ? and is_read = 0", m.baseModel.table), userID, otherID)
	return count, err
}

func (m *customChatMessagesModel) GetAllUnreadCounts(ctx context.Context, userID int64) (map[int64]int64, error) {
	var rows []struct {
		SenderID int64 `db:"sender_id"`
		Count    int64 `db:"count"`
	}
	query := fmt.Sprintf("select sender_id, count(*) as count from %s where receiver_id = ? and is_read = 0 group by sender_id", m.baseModel.table)
	if err := m.conn.QueryRowsCtx(ctx, &rows, query, userID); err != nil {
		return nil, err
	}
	result := make(map[int64]int64)
	for _, row := range rows {
		result[row.SenderID] = row.Count
	}
	return result, nil
}

func (m *customChatMessagesModel) MarkAsRead(ctx context.Context, messageID uint64) error {
	_, err := m.conn.ExecCtx(ctx, fmt.Sprintf("update %s set is_read = 1 where id = ?", m.baseModel.table), messageID)
	return err
}

func (m *customChatMessagesModel) MarkChatHistoryAsRead(ctx context.Context, userID, otherID int64) error {
	_, err := m.conn.ExecCtx(ctx, fmt.Sprintf("update %s set is_read = 1 where receiver_id = ? and sender_id = ?", m.baseModel.table), userID, otherID)
	return err
}

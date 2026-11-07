package chatMessages

import (
	"context"
	"database/sql"
	"fmt"

	"github.com/zeromicro/go-zero/core/stores/sqlx"
)

var _ ChatMessagesModel = (*customChatMessagesModel)(nil)

type (
	// ChatMessagesModel 聊天消息数据访问接口，提供消息 CRUD、历史分页查询、未读统计与已读标记能力
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
		MarkChatHistoryAsReadThrough(context.Context, int64, int64, uint64) error
	}
	// customChatMessagesModel 聊天消息模型的默认实现，组合数据库连接与生成的基础模型
	customChatMessagesModel struct {
		conn      sqlx.SqlConn
		baseModel *defaultChatMessagesModel
	}
)

// NewChatMessagesModel 创建聊天消息模型实例
func NewChatMessagesModel(conn sqlx.SqlConn) ChatMessagesModel {
	return &customChatMessagesModel{conn: conn, baseModel: newChatMessagesModel(conn)}
}

// Insert 插入一条聊天消息
func (m *customChatMessagesModel) Insert(ctx context.Context, data *ChatMessages) error {
	_, err := m.insert(ctx, data)
	return err
}

// insert 执行插入并返回结果集，供需要回填自增主键的调用方复用
// conversation_low/conversation_high 是虚拟生成列，显式写入（含写 NULL）会被 MySQL 拒绝并报 3105 错误，
// goctl 生成的 baseModel.Insert 会把这两列一起写进去，这里只写业务列，会话键交给数据库计算
func (m *customChatMessagesModel) insert(ctx context.Context, data *ChatMessages) (sql.Result, error) {
	query := fmt.Sprintf(
		"insert into %s (sender_id, receiver_id, content, is_read) values (?, ?, ?, ?)",
		m.baseModel.table,
	)
	return m.conn.ExecCtx(ctx, query, data.SenderId, data.ReceiverId, data.Content, data.IsRead)
}

// FindOne 按主键查询聊天消息
func (m *customChatMessagesModel) FindOne(ctx context.Context, id uint64) (*ChatMessages, error) {
	return m.baseModel.FindOne(ctx, id)
}

// Update 更新聊天消息记录
// created_at 由数据库默认值生成、conversation_low/conversation_high 为生成列，三者都不能出现在 set 子句里
func (m *customChatMessagesModel) Update(ctx context.Context, data *ChatMessages) error {
	query := fmt.Sprintf(
		"update %s set sender_id = ?, receiver_id = ?, content = ?, is_read = ? where id = ?",
		m.baseModel.table,
	)
	_, err := m.conn.ExecCtx(ctx, query, data.SenderId, data.ReceiverId, data.Content, data.IsRead, data.Id)
	return err
}

// Delete 按主键删除聊天消息
func (m *customChatMessagesModel) Delete(ctx context.Context, id uint64) error {
	return m.baseModel.Delete(ctx, id)
}

// CreateChatMessage 插入聊天消息并把数据库生成的 id、created_at 等字段回写到入参对象
func (m *customChatMessagesModel) CreateChatMessage(ctx context.Context, message *ChatMessages) error {
	result, err := m.insert(ctx, message)
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

// GetChatHistory 分页查询两人之间的聊天记录并返回消息总数，按创建时间升序排列
// 会话键用虚拟生成列 conversation_low/conversation_high 表达，等值命中 idx_conversation_created 并免排序
func (m *customChatMessagesModel) GetChatHistory(ctx context.Context, userID, otherID int64, offset, limit int) ([]*ChatMessages, int64, error) {
	low, high := userID, otherID
	if low > high {
		low, high = high, low
	}
	where := "conversation_low = ? and conversation_high = ?"

	var total int64
	countQuery := fmt.Sprintf("select count(*) from %s where %s", m.baseModel.table, where)
	if err := m.conn.QueryRowCtx(ctx, &total, countQuery, low, high); err != nil {
		return nil, 0, err
	}
	var messages []ChatMessages
	dataQuery := fmt.Sprintf("select %s from %s where %s order by created_at asc, id asc limit ? offset ?", chatMessagesRows, m.baseModel.table, where)
	if err := m.conn.QueryRowsCtx(ctx, &messages, dataQuery, low, high, limit, offset); err != nil {
		return nil, 0, err
	}
	result := make([]*ChatMessages, 0, len(messages))
	for i := range messages {
		result = append(result, &messages[i])
	}
	return result, total, nil
}

// GetUnreadCount 统计指定用户收到来自另一用户的未读消息数
func (m *customChatMessagesModel) GetUnreadCount(ctx context.Context, userID, otherID int64) (int64, error) {
	var count int64
	err := m.conn.QueryRowCtx(ctx, &count, fmt.Sprintf("select count(*) from %s where receiver_id = ? and sender_id = ? and is_read = 0", m.baseModel.table), userID, otherID)
	return count, err
}

// GetAllUnreadCounts 按发送者分组统计用户收到的全部未读消息数
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

// MarkAsRead 按消息 id 将单条消息标记为已读
func (m *customChatMessagesModel) MarkAsRead(ctx context.Context, messageID uint64) error {
	_, err := m.conn.ExecCtx(ctx, fmt.Sprintf("update %s set is_read = 1 where id = ?", m.baseModel.table), messageID)
	return err
}

// MarkChatHistoryAsRead 将用户收到来自另一用户的全部消息标记为已读
func (m *customChatMessagesModel) MarkChatHistoryAsRead(ctx context.Context, userID, otherID int64) error {
	_, err := m.conn.ExecCtx(ctx, fmt.Sprintf("update %s set is_read = 1 where receiver_id = ? and sender_id = ?", m.baseModel.table), userID, otherID)
	return err
}

// MarkChatHistoryAsReadThrough 将指定会话中 id 不超过 lastMessageID 的未读消息批量标记为已读
func (m *customChatMessagesModel) MarkChatHistoryAsReadThrough(
	ctx context.Context,
	userID int64,
	otherID int64,
	lastMessageID uint64,
) error {
	query := fmt.Sprintf(
		"update %s set is_read = 1 where receiver_id = ? and sender_id = ? and id <= ? and is_read = 0",
		m.baseModel.table,
	)
	_, err := m.conn.ExecCtx(ctx, query, userID, otherID, lastMessageID)
	return err
}

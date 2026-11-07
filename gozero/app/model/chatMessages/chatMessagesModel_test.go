package chatMessages

import (
	"context"
	"database/sql"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/zeromicro/go-zero/core/stores/sqlx"
)

// insertResult 固定自增主键与影响行数的 sql.Result 替身
type insertResult struct{}

// LastInsertId 返回固定主键，供回填逻辑断言
func (insertResult) LastInsertId() (int64, error) { return 42, nil }

// RowsAffected 返回固定影响行数
func (insertResult) RowsAffected() (int64, error) { return 1, nil }

// recordConn 记录 ExecCtx 收到的 SQL 与参数，未使用的方法由嵌入的接口兜底
type recordConn struct {
	sqlx.SqlConn
	execQuery string
	execArgs  []any
}

// ExecCtx 记录 SQL 与参数并返回固定结果
func (c *recordConn) ExecCtx(_ context.Context, query string, args ...any) (sql.Result, error) {
	c.execQuery = query
	c.execArgs = args
	return insertResult{}, nil
}

// QueryRowCtx 填充固定记录，模拟插入后按主键回查
func (c *recordConn) QueryRowCtx(_ context.Context, v any, _ string, _ ...any) error {
	if message, ok := v.(*ChatMessages); ok {
		*message = ChatMessages{Id: 42, SenderId: 1, ReceiverId: 2, Content: "hello"}
	}
	return nil
}

// newRecordModel 组合记录型连接构造模型实例
func newRecordModel() (*customChatMessagesModel, *recordConn) {
	conn := &recordConn{}
	return &customChatMessagesModel{conn: conn, baseModel: newChatMessagesModel(conn)}, conn
}

// TestCustomChatMessagesModelInsertSkipsGeneratedColumns 校验插入语句不写虚拟生成列，避免 MySQL 报 3105
func TestCustomChatMessagesModelInsertSkipsGeneratedColumns(t *testing.T) {
	model, conn := newRecordModel()

	err := model.Insert(context.Background(), &ChatMessages{SenderId: 1, ReceiverId: 2, Content: "hello"})

	assert.NoError(t, err)
	assert.NotContains(t, conn.execQuery, "conversation_low")
	assert.NotContains(t, conn.execQuery, "conversation_high")
	assert.NotContains(t, conn.execQuery, "created_at")
	assert.Equal(t, []any{int64(1), int64(2), "hello", int64(0)}, conn.execArgs)
}

// TestCustomChatMessagesModelUpdateSkipsGeneratedColumns 校验更新语句不写生成列与 created_at
func TestCustomChatMessagesModelUpdateSkipsGeneratedColumns(t *testing.T) {
	model, conn := newRecordModel()

	err := model.Update(context.Background(), &ChatMessages{Id: 7, SenderId: 1, ReceiverId: 2, Content: "hello", IsRead: 1})

	assert.NoError(t, err)
	assert.NotContains(t, conn.execQuery, "conversation_low")
	assert.NotContains(t, conn.execQuery, "conversation_high")
	assert.NotContains(t, conn.execQuery, "created_at")
	assert.Equal(t, []any{int64(1), int64(2), "hello", int64(1), uint64(7)}, conn.execArgs)
}

// TestCustomChatMessagesModelCreateChatMessageBackfillsId 校验插入后回填自增主键，且插入语句同样不写生成列
func TestCustomChatMessagesModelCreateChatMessageBackfillsId(t *testing.T) {
	model, conn := newRecordModel()
	message := &ChatMessages{SenderId: 1, ReceiverId: 2, Content: "hello"}

	err := model.CreateChatMessage(context.Background(), message)

	assert.NoError(t, err)
	assert.NotContains(t, conn.execQuery, "conversation_low")
	assert.Equal(t, uint64(42), message.Id)
}

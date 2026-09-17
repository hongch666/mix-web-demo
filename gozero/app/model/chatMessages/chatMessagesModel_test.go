package chatMessages

import (
	"context"
	"errors"
	"regexp"
	"testing"

	"github.com/DATA-DOG/go-sqlmock"
	"github.com/zeromicro/go-zero/core/stores/sqlx"
)

func TestMarkChatHistoryAsReadThrough(t *testing.T) {
	db, mock, err := sqlmock.New()
	if err != nil {
		t.Fatalf("创建数据库 Mock 失败: %v", err)
	}
	t.Cleanup(func() { _ = db.Close() })
	model := NewChatMessagesModel(sqlx.NewSqlConnFromDB(db))
	query := regexp.QuoteMeta(
		"update `chat_messages` set is_read = 1 where receiver_id = ? and sender_id = ? and id <= ? and is_read = 0",
	)
	mock.ExpectExec(query).
		WithArgs(int64(7), int64(8), uint64(42)).
		WillReturnResult(sqlmock.NewResult(0, 3))

	if err := model.MarkChatHistoryAsReadThrough(context.Background(), 7, 8, 42); err != nil {
		t.Fatalf("标记聊天历史已读失败: %v", err)
	}
	if err := mock.ExpectationsWereMet(); err != nil {
		t.Fatalf("SQL 调用不符合预期: %v", err)
	}
}

func TestMarkChatHistoryAsReadThroughReturnsDatabaseError(t *testing.T) {
	db, mock, err := sqlmock.New()
	if err != nil {
		t.Fatalf("创建数据库 Mock 失败: %v", err)
	}
	t.Cleanup(func() { _ = db.Close() })
	model := NewChatMessagesModel(sqlx.NewSqlConnFromDB(db))
	databaseError := errors.New("database unavailable")
	mock.ExpectExec("update `chat_messages`").WillReturnError(databaseError)

	err = model.MarkChatHistoryAsReadThrough(context.Background(), 7, 8, 42)
	if !errors.Is(err, databaseError) {
		t.Fatalf("返回错误 = %v, 期望 %v", err, databaseError)
	}
}

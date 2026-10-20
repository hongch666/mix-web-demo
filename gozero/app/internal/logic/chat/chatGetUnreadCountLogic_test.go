package chat

import (
	"context"
	"errors"
	"testing"

	"app/internal/types"
)

// 验证获取两人间未读数时透传用户参数和查询结果
func TestChatGetUnreadCountPassesUsersAndReturnsCount(t *testing.T) {
	model := &chatMessageModelFake{singleUnread: 5}
	ctx, _ := newChatMessageTestContext(t, model, false)
	logic := NewChatGetUnreadCountLogic(context.Background(), ctx)
	t.Cleanup(func() { _ = logic.ZeroLogger.Close() })

	response, err := logic.ChatGetUnreadCount(&types.ChatGetUnreadCountReq{UserId: 2, OtherId: 1})
	if err != nil || response == nil || response.UnreadCount != 5 {
		t.Fatalf("未读数结果不正确: %+v, %v", response, err)
	}
	if model.singleUserID != 2 || model.singleOtherID != 1 {
		t.Fatalf("查询参数不正确: userID=%d otherID=%d", model.singleUserID, model.singleOtherID)
	}
}

// 验证获取两人间未读数查询失败时返回错误
func TestChatGetUnreadCountReportsQueryFailure(t *testing.T) {
	model := &chatMessageModelFake{singleErr: errors.New("read failed")}
	ctx, _ := newChatMessageTestContext(t, model, false)
	logic := NewChatGetUnreadCountLogic(context.Background(), ctx)
	t.Cleanup(func() { _ = logic.ZeroLogger.Close() })

	response, err := logic.ChatGetUnreadCount(&types.ChatGetUnreadCountReq{UserId: 2, OtherId: 1})
	if err == nil || response != nil {
		t.Fatalf("查询失败应返回错误: %+v, %v", response, err)
	}
}

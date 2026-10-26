package chat

import (
	"context"
	"errors"
	"testing"

	"app/internal/testkit"
	"app/internal/types"
)

// 验证获取两人间未读数时透传用户参数和查询结果
func TestChatGetUnreadCountPassesUsersAndReturnsCount(t *testing.T) {
	model := &testkit.ChatMessageModelFake{SingleUnread: 5}
	ctx, _ := testkit.NewChatMessageTestContext(t, model, false)
	logic := NewChatGetUnreadCountLogic(context.Background(), ctx)
	t.Cleanup(func() { _ = logic.ZeroLogger.Close() })

	response, err := logic.ChatGetUnreadCount(&types.ChatGetUnreadCountReq{UserId: 2, OtherId: 1})
	if err != nil || response == nil || response.UnreadCount != 5 {
		t.Fatalf("未读数结果不正确: %+v, %v", response, err)
	}
	if model.SingleUserID != 2 || model.SingleOtherID != 1 {
		t.Fatalf("查询参数不正确: userID=%d otherID=%d", model.SingleUserID, model.SingleOtherID)
	}
}

// 验证获取两人间未读数查询失败时返回错误
func TestChatGetUnreadCountReportsQueryFailure(t *testing.T) {
	model := &testkit.ChatMessageModelFake{SingleErr: errors.New("read failed")}
	ctx, _ := testkit.NewChatMessageTestContext(t, model, false)
	logic := NewChatGetUnreadCountLogic(context.Background(), ctx)
	t.Cleanup(func() { _ = logic.ZeroLogger.Close() })

	response, err := logic.ChatGetUnreadCount(&types.ChatGetUnreadCountReq{UserId: 2, OtherId: 1})
	if err == nil || response != nil {
		t.Fatalf("查询失败应返回错误: %+v, %v", response, err)
	}
}

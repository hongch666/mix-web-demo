package chat

import (
	"context"
	"errors"
	"testing"

	"app/internal/testkit"
	"app/internal/types"
)

// 验证获取所有未读数时透传模型查询结果
func TestChatGetAllUnreadCountsReturnsModelData(t *testing.T) {
	model := &testkit.ChatMessageModelFake{Unread: map[int64]int64{1: 3, 5: 2}}
	ctx, _ := testkit.NewChatMessageTestContext(t, model, false)
	logic := NewChatGetAllUnreadCountsLogic(context.Background(), ctx)
	t.Cleanup(func() { _ = logic.ZeroLogger.Close() })

	response, err := logic.ChatGetAllUnreadCounts(&types.ChatGetAllUnreadCountsReq{UserId: 2})
	if err != nil || response == nil || len(response.Data) != 2 || response.Data[1] != 3 || response.Data[5] != 2 {
		t.Fatalf("未读数结果不正确: %+v, %v", response, err)
	}
}

// 验证获取所有未读数查询失败时返回错误
func TestChatGetAllUnreadCountsReportsQueryFailure(t *testing.T) {
	model := &testkit.ChatMessageModelFake{UnreadErr: errors.New("read failed")}
	ctx, _ := testkit.NewChatMessageTestContext(t, model, false)
	logic := NewChatGetAllUnreadCountsLogic(context.Background(), ctx)
	t.Cleanup(func() { _ = logic.ZeroLogger.Close() })

	response, err := logic.ChatGetAllUnreadCounts(&types.ChatGetAllUnreadCountsReq{UserId: 2})
	if err == nil || response != nil {
		t.Fatalf("查询失败应返回错误: %+v, %v", response, err)
	}
}

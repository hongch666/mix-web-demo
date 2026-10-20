package chat

import (
	"context"
	"testing"

	"app/internal/hub"
	"app/internal/svc"
	"app/internal/types"
)

// 验证聊天用户加入队列后重复加入会返回不同状态
func TestChatJoinQueueReportsDuplicateUser(t *testing.T) {
	logger := newChatTestLogger(t)
	chatHub := &hub.ChatHub{ZeroLogger: logger}
	logic := NewChatJoinQueueLogic(context.Background(), &svc.ServiceContext{HubContext: &svc.HubContext{ChatHub: chatHub}, LoggerContext: &svc.LoggerContext{Logger: logger}})
	t.Cleanup(func() { _ = logic.ZeroLogger.Close() })

	first, err := logic.ChatJoinQueue(&types.ChatJoinQueueReq{UserId: 900001})
	if err != nil || first.Status == "" {
		t.Fatalf("首次加入队列失败: %+v, %v", first, err)
	}
	defer chatHub.LeaveQueue(900001)
	second, err := logic.ChatJoinQueue(&types.ChatJoinQueueReq{UserId: 900001})
	if err != nil || second.Status == first.Status {
		t.Fatalf("重复加入状态不正确: %+v, %v", second, err)
	}
}

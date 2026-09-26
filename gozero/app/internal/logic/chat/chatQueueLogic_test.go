package chat

import (
	"context"
	"testing"

	"app/common/utils"
	"app/internal/hub"
	"app/internal/svc"
	"app/internal/types"
)

// 验证聊天用户加入队列后重复加入会返回不同状态
func TestChatJoinQueueReportsDuplicateUser(t *testing.T) {
	logger, err := utils.NewZeroLogger(t.TempDir())
	if err != nil {
		t.Fatalf("创建测试日志器失败: %v", err)
	}
	t.Cleanup(func() { _ = logger.Close() })
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

// 验证聊天用户离开队列后返回离开状态
func TestChatLeaveQueueRemovesUser(t *testing.T) {
	logger, err := utils.NewZeroLogger(t.TempDir())
	if err != nil {
		t.Fatalf("创建测试日志器失败: %v", err)
	}
	t.Cleanup(func() { _ = logger.Close() })
	chatHub := &hub.ChatHub{ZeroLogger: logger}
	chatHub.JoinQueue(900002, &hub.Client{UserID: 900002, Send: make(chan []byte, 1)})
	logic := NewChatLeaveQueueLogic(context.Background(), &svc.ServiceContext{HubContext: &svc.HubContext{ChatHub: chatHub}, LoggerContext: &svc.LoggerContext{Logger: logger}})
	t.Cleanup(func() { _ = logic.ZeroLogger.Close() })
	resp, err := logic.ChatLeaveQueue(&types.ChatLeaveQueueReq{UserId: 900002})
	if err != nil || resp.Status == "" || chatHub.IsUserInQueue(900002) {
		t.Fatalf("离开队列结果不正确: %+v, %v", resp, err)
	}
}

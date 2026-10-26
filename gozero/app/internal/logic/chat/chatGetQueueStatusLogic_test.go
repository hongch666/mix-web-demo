package chat

import (
	"context"
	"testing"

	"app/common/testkit"
	"app/internal/hub"
	"app/internal/svc"
)

// 验证获取队列状态时返回队列中的全部用户及数量
func TestChatGetQueueStatusListsQueueUsers(t *testing.T) {
	logger := testkit.NewTestLogger(t)
	chatHub := hub.NewChatHub(logger)
	chatHub.JoinQueue(900003, &hub.Client{UserID: 900003, Send: make(chan []byte, 1)})
	chatHub.JoinQueue(900004, &hub.Client{UserID: 900004, Send: make(chan []byte, 1)})
	t.Cleanup(func() {
		chatHub.LeaveQueue(900003)
		chatHub.LeaveQueue(900004)
	})
	logic := NewChatGetQueueStatusLogic(context.Background(), &svc.ServiceContext{HubContext: &svc.HubContext{ChatHub: chatHub}, LoggerContext: &svc.LoggerContext{Logger: logger}})
	t.Cleanup(func() { _ = logic.ZeroLogger.Close() })

	resp, err := logic.ChatGetQueueStatus()
	if err != nil || resp == nil || resp.Count != 2 || len(resp.OnlineUsers) != 2 {
		t.Fatalf("队列状态结果不正确: %+v, %v", resp, err)
	}
	inQueue := map[int64]bool{resp.OnlineUsers[0]: true, resp.OnlineUsers[1]: true}
	if !inQueue[900003] || !inQueue[900004] {
		t.Fatalf("队列用户列表不正确: %v", resp.OnlineUsers)
	}
}

// 验证队列为空时返回零计数
func TestChatGetQueueStatusReportsEmptyQueue(t *testing.T) {
	logger := testkit.NewTestLogger(t)
	chatHub := hub.NewChatHub(logger)
	logic := NewChatGetQueueStatusLogic(context.Background(), &svc.ServiceContext{HubContext: &svc.HubContext{ChatHub: chatHub}, LoggerContext: &svc.LoggerContext{Logger: logger}})
	t.Cleanup(func() { _ = logic.ZeroLogger.Close() })

	resp, err := logic.ChatGetQueueStatus()
	if err != nil || resp == nil || resp.Count != 0 || len(resp.OnlineUsers) != 0 {
		t.Fatalf("空队列状态不正确: %+v, %v", resp, err)
	}
}

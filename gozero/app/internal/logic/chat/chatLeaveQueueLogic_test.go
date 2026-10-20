package chat

import (
	"context"
	"testing"

	"app/internal/hub"
	"app/internal/svc"
	"app/internal/types"
)

// 验证聊天用户离开队列后返回离开状态
func TestChatLeaveQueueRemovesUser(t *testing.T) {
	logger := newChatTestLogger(t)
	chatHub := &hub.ChatHub{ZeroLogger: logger}
	chatHub.JoinQueue(900002, &hub.Client{UserID: 900002, Send: make(chan []byte, 1)})
	logic := NewChatLeaveQueueLogic(context.Background(), &svc.ServiceContext{HubContext: &svc.HubContext{ChatHub: chatHub}, LoggerContext: &svc.LoggerContext{Logger: logger}})
	t.Cleanup(func() { _ = logic.ZeroLogger.Close() })

	resp, err := logic.ChatLeaveQueue(&types.ChatLeaveQueueReq{UserId: 900002})
	if err != nil || resp.Status == "" || chatHub.IsUserInQueue(900002) {
		t.Fatalf("离开队列结果不正确: %+v, %v", resp, err)
	}
}

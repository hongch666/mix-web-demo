package testkit

import (
	"context"
	"testing"

	"app/common/pubsub"
	commontestkit "app/common/testkit"
	"app/internal/hub"
	"app/internal/svc"
	"app/model/chatMessages"
)

// NewChatMessageTestContext 组装带消息模型替身与实时 Hub 的最小 ServiceContext，并返回接收者的通知通道
//
// withBrokenBus 为 true 时挂载不可用的 Redis 广播总线，用于验证跨实例发布失败后本地链路仍然可用
func NewChatMessageTestContext(t *testing.T, model chatMessages.ChatMessagesModel, withBrokenBus bool) (*svc.ServiceContext, chan any) {
	t.Helper()
	logger := commontestkit.NewTestLogger(t)
	sseHub := hub.NewSSEHub(logger)
	notifications := make(chan any, 1)
	sseHub.RegisterClient(context.Background(), 2, "receiver", notifications, make(chan bool))
	chatHub := hub.NewChatHub(logger)
	hubContext := &svc.HubContext{
		ChatHub:            chatHub,
		SSEHub:             sseHub,
		RealtimeDispatcher: hub.NewChatRealtimeDispatcher(chatHub, sseHub, logger),
	}
	if withBrokenBus {
		hubContext.RealtimeBus = pubsub.NewRedisPubSub(nil, logger, "chat-events")
	}
	return &svc.ServiceContext{
		ModelContext:  &svc.ModelContext{ChatMessagesModel: model},
		HubContext:    hubContext,
		LoggerContext: &svc.LoggerContext{Logger: logger},
	}, notifications
}

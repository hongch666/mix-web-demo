package hub

import (
	"context"
	"encoding/json"
	"fmt"

	"app/common/constants"
	"app/common/utils"
)

// ChatRealtimeDispatcher 负责处理跨 Pod 的聊天实时事件
type ChatRealtimeDispatcher struct {
	chatHub *ChatHub
	sseHub  *SSEHubManager
	logger  *utils.ZeroLogger
}

// NewChatRealtimeDispatcher 创建聊天实时事件分发器
func NewChatRealtimeDispatcher(
	chatHub *ChatHub,
	sseHub *SSEHubManager,
	logger *utils.ZeroLogger,
) *ChatRealtimeDispatcher {
	return &ChatRealtimeDispatcher{
		chatHub: chatHub,
		sseHub:  sseHub,
		logger:  logger,
	}
}

// Handle 处理一条聊天实时事件，并投递到当前 Pod 的连接
// ctx 由事件来源提供：Redis 订阅回调用服务上下文，同进程发送用当前请求的上下文
func (d *ChatRealtimeDispatcher) Handle(ctx context.Context, payload []byte) {
	if d == nil {
		return
	}

	var event ChatRealtimeEvent
	if err := json.Unmarshal(payload, &event); err != nil {
		d.logError(ctx, fmt.Sprintf(constants.REDIS_REALTIME_MESSAGE_ERROR, err))
		return
	}

	if event.ReceiverID <= 0 || event.WebSocketMessage == nil || event.SSENotification == nil {
		d.logError(ctx, constants.REDIS_REALTIME_INVALID_MESSAGE_FORMAT_ERROR)
		return
	}

	messageBytes, err := json.Marshal(event.WebSocketMessage)
	if err != nil {
		d.logError(ctx, fmt.Sprintf(constants.REDIS_REALTIME_MESSAGE_ERROR, err))
		return
	}

	if d.chatHub != nil && d.chatHub.SendMessageToQueue(ctx, event.ReceiverID, messageBytes) {
		return
	}

	if d.sseHub != nil {
		d.sseHub.SendNotificationToUser(ctx, event.ReceiverID, event.SSENotification)
	}
}

// logError 记录实时事件分发过程中的错误日志，分发器或日志器未初始化时静默跳过
func (d *ChatRealtimeDispatcher) logError(ctx context.Context, message string) {
	if d == nil || d.logger == nil {
		return
	}
	d.logger.WithContext(ctx).Error(message)
}

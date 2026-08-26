package realtime

import (
	"context"
	"encoding/json"
	"fmt"

	"app/common/constants"
	"app/common/hub"
	"app/common/utils"

	"github.com/zeromicro/go-zero/core/logx"
)

type chatHistoryReader interface {
	MarkChatHistoryAsRead(context.Context, int64, int64) error
}

// ChatRealtimeDispatcher 负责处理跨 Pod 的聊天实时事件。
type ChatRealtimeDispatcher struct {
	ctx               context.Context
	chatHub           *hub.ChatHub
	sseHub            *hub.SSEHubManager
	chatHistoryReader chatHistoryReader
	logger            *utils.ZeroLogger
}

// NewChatRealtimeDispatcher 创建聊天实时事件分发器。
func NewChatRealtimeDispatcher(
	ctx context.Context,
	chatHub *hub.ChatHub,
	sseHub *hub.SSEHubManager,
	chatHistoryReader chatHistoryReader,
	logger *utils.ZeroLogger,
) *ChatRealtimeDispatcher {
	return &ChatRealtimeDispatcher{
		ctx:               ctx,
		chatHub:           chatHub,
		sseHub:            sseHub,
		chatHistoryReader: chatHistoryReader,
		logger:            logger,
	}
}

// Handle 处理一条聊天实时事件，并投递到当前 Pod 的连接。
func (d *ChatRealtimeDispatcher) Handle(payload []byte) {
	if d == nil {
		return
	}

	var event hub.ChatRealtimeEvent
	if err := json.Unmarshal(payload, &event); err != nil {
		d.logError(fmt.Sprintf(constants.REDIS_REALTIME_MESSAGE_ERROR, err))
		return
	}

	if event.ReceiverID <= 0 || event.WebSocketMessage == nil || event.SSENotification == nil {
		d.logError(constants.REDIS_REALTIME_INVALID_MESSAGE_FORMAT_ERROR)
		return
	}

	messageBytes, err := json.Marshal(event.WebSocketMessage)
	if err != nil {
		d.logError(fmt.Sprintf(constants.REDIS_REALTIME_MESSAGE_ERROR, err))
		return
	}

	if d.chatHub != nil && d.chatHub.SendMessageToQueue(event.ReceiverID, messageBytes) {
		d.markChatHistoryAsRead(event.WebSocketMessage.SenderID, event.ReceiverID)
		return
	}

	if d.sseHub != nil {
		d.sseHub.SendNotificationToUser(event.ReceiverID, event.SSENotification)
	}
}

func (d *ChatRealtimeDispatcher) markChatHistoryAsRead(senderID, receiverID int64) {
	if d.chatHistoryReader == nil {
		return
	}

	if err := d.chatHistoryReader.MarkChatHistoryAsRead(d.ctx, senderID, receiverID); err != nil {
		d.logError(fmt.Sprintf(constants.MARK_MESSAGE_READ_ERROR, err))
	}
}

func (d *ChatRealtimeDispatcher) logError(message string) {
	if d.logger != nil {
		d.logger.Error(message)
		return
	}
	logx.Error(message)
}

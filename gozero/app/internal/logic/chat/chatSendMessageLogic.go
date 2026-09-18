// Code scaffolded by goctl. Safe to edit.
// goctl 1.9.2

package chat

import (
	"context"
	"encoding/json"
	"fmt"
	"strings"
	"time"

	"app/common/constants"
	"app/common/exceptions"
	"app/common/utils"
	"app/internal/hub"
	"app/internal/svc"
	"app/internal/types"
	"app/model/chatMessages"
)

type ChatSendMessageLogic struct {
	ctx    context.Context
	svcCtx *svc.ServiceContext
	*utils.ZeroLogger
}

// 发送消息
func NewChatSendMessageLogic(ctx context.Context, svcCtx *svc.ServiceContext) *ChatSendMessageLogic {
	return &ChatSendMessageLogic{
		ctx:        ctx,
		svcCtx:     svcCtx,
		ZeroLogger: svcCtx.Logger.WithContext(ctx),
	}
}

func (l *ChatSendMessageLogic) ChatSendMessage(req *types.ChatSendMessageReq) (resp *types.ChatSendMessageResp, err error) {
	// 校验器只负责边界检查，内容在此统一去除首尾空白后再落库与推送
	content := strings.TrimSpace(req.Content)

	// 创建聊天消息
	message := &chatMessages.ChatMessages{
		SenderId:   req.SenderId,
		ReceiverId: req.ReceiverId,
		Content:    content,
		IsRead:     0, // 初始为未读
	}

	if err := l.svcCtx.ChatMessagesModel.CreateChatMessage(l.ctx, message); err != nil {
		l.Error(fmt.Sprintf(constants.CREATE_MESSAGE_ERROR+": %v", err))
		return nil, exceptions.NewInternalServerError(constants.CREATE_MESSAGE_ERROR, err.Error())
	}

	l.Info(constants.CHAT_MESSAGE_SEND_SUCCESS)

	// 2. 检查接收者的所有WebSocket连接，如果存在就统一投递
	wsMessage := &types.ChatWsMessage{
		Type:       "message",
		SenderId:   req.SenderId,
		ReceiverId: req.ReceiverId,
		Content:    content,
		MessageId:  uint64(message.Id),
		Timestamp:  time.Now().Format(constants.DateTimeFormat),
	}

	unreadCounts, err := l.svcCtx.ChatMessagesModel.GetAllUnreadCounts(l.ctx, req.ReceiverId)
	if err != nil {
		l.Error(fmt.Sprintf(constants.GET_UNREAD_COUNT_MESSAGE_ERROR, err))
		unreadCounts = make(map[int64]int64)
	}

	notification := &types.ChatSSEMessage{
		Type:         "message",
		UserId:       req.ReceiverId,
		UnreadCounts: unreadCounts,
		Message: &types.ChatMessageItem{
			Id:         uint64(message.Id),
			SenderId:   message.SenderId,
			ReceiverId: message.ReceiverId,
			Content:    message.Content,
			IsRead:     int8(message.IsRead),
			CreatedAt:  message.CreatedAt.Format(constants.DateTimeFormat),
		},
	}

	event := &hub.ChatRealtimeEvent{
		Type:             "chat.message",
		ReceiverID:       req.ReceiverId,
		WebSocketMessage: wsMessage,
		SSENotification:  notification,
	}
	eventBytes, err := json.Marshal(event)
	if err != nil {
		l.Error(fmt.Sprintf(constants.WS_SERIALIZE_MESSAGE_ERROR, err))
		return nil, exceptions.NewInternalServerError(constants.MESSAGE_SEND_ERROR, err.Error())
	}

	if l.svcCtx.RealtimeBus == nil {
		l.svcCtx.RealtimeDispatcher.Handle(eventBytes)
	} else {
		if err := l.svcCtx.RealtimeBus.Publish(l.ctx, eventBytes); err != nil {
			l.Error(fmt.Sprintf(constants.REDIS_REALTIME_PUBLISH_ERROR, err))
			l.svcCtx.RealtimeDispatcher.Handle(eventBytes)
		}
	}

	resp = &types.ChatSendMessageResp{
		MessageId: message.Id,
	}

	return
}

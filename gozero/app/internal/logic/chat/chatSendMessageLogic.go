// Code scaffolded by goctl. Safe to edit.
// goctl 1.9.2

package chat

import (
	"context"
	"encoding/json"
	"fmt"
	"time"

	"app/common/exceptions"
	"app/common/logger"
	"app/common/utils"
	"app/dto"
	"app/internal/svc"
	"app/internal/types"
	"app/model/chatMessages"
)

type ChatSendMessageLogic struct {
	ctx    context.Context
	svcCtx *svc.ServiceContext
	logger *logger.ZeroLogger
}

// 发送消息
func NewChatSendMessageLogic(ctx context.Context, svcCtx *svc.ServiceContext) *ChatSendMessageLogic {
	return &ChatSendMessageLogic{
		ctx:    ctx,
		svcCtx: svcCtx,
		logger: svcCtx.Logger,
	}
}

func (l *ChatSendMessageLogic) ChatSendMessage(req *types.ChatSendMessageReq) (resp *types.ChatSendMessageResp, err error) {
	// 创建聊天消息
	message := &chatMessages.ChatMessages{
		SenderId:   req.SenderId,
		ReceiverId: req.ReceiverId,
		Content:    req.Content,
		IsRead:     0, // 初始为未读
	}

	if err := l.svcCtx.ChatMessagesModel.CreateChatMessage(l.ctx, message); err != nil {
		l.svcCtx.Logger.Error(fmt.Sprintf(utils.CREATE_MESSAGE_ERROR+": %v", err))
		panic(exceptions.NewBusinessError(utils.CREATE_MESSAGE_ERROR, err.Error()))
	}

	l.logger.Info(utils.CHAT_MESSAGE_SEND_SUCCESS)

	// 2. 检查接收者是否在队列中，如果在就通过WebSocket发送
	if l.svcCtx.ChatHub.IsUserInQueue(req.ReceiverId) {
		wsMessage := &dto.WebSocketMessage{
			Type:       "message",
			SenderID:   req.SenderId,
			ReceiverID: req.ReceiverId,
			Content:    req.Content,
			MessageID:  uint(message.Id),
			Timestamp:  time.Now().Format("2006-01-02 15:04:05"),
		}

		messageBytes, _ := json.Marshal(wsMessage)
		if l.svcCtx.ChatHub.SendMessageToQueue(req.ReceiverId, messageBytes) {
			// 发送成功，消息已读
			l.svcCtx.ChatMessagesModel.MarkChatHistoryAsRead(l.ctx, req.SenderId, req.ReceiverId)
			l.logger.Info(fmt.Sprintf(utils.WS_SEND_SUCCESS, message.Id))
		} else {
			// 发送失败，用户可能刷离线，消息保持未读
			l.logger.Error(fmt.Sprintf(utils.WS_SEND_FAIL, req.ReceiverId, message.Id))
			// 触发SSE通知发送未读消息
			go l.notifyUnreadMessage(req.ReceiverId, req.SenderId, message)
		}
	} else {
		l.logger.Error(fmt.Sprintf(utils.WS_SEND_FAIL, req.ReceiverId, message.Id))
		// 触发SSE通知发送未读消息
		go l.notifyUnreadMessage(req.ReceiverId, req.SenderId, message)
	}

	resp = &types.ChatSendMessageResp{
		MessageID: message.Id,
	}

	return
}

// notifyUnreadMessage 通知用户有新的未读消息
func (l *ChatSendMessageLogic) notifyUnreadMessage(userID, _ string, message *chatMessages.ChatMessages) {
	// 获取该用户的所有未读消息数
	unreadCounts, err := l.svcCtx.ChatMessagesModel.GetAllUnreadCounts(l.ctx, userID)
	if err != nil {
		l.svcCtx.Logger.Error(fmt.Sprintf(utils.GET_UNREAD_COUNT_MESSAGE_ERROR, err))
		return
	}

	notification := &dto.SSEMessageNotification{
		Type:         "message",
		UserID:       userID,
		UnreadCounts: unreadCounts,
		Message: &dto.ChatMessageItem{
			ID:         uint(message.Id),
			SenderID:   message.SenderId,
			ReceiverID: message.ReceiverId,
			Content:    message.Content,
			IsRead:     int8(message.IsRead),
			CreatedAt:  message.CreatedAt.Format("2006-01-02 15:04:05"),
		},
	}

	l.svcCtx.SSEHub.SendNotificationToUser(userID, notification)
}

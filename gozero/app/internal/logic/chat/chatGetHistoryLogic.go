// Code scaffolded by goctl. Safe to edit.
// goctl 1.9.2

package chat

import (
	"context"
	"fmt"

	"app/common/exceptions"
	"app/common/logger"
	"app/common/utils"
	"app/internal/svc"
	"app/internal/types"
)

type ChatGetHistoryLogic struct {
	ctx    context.Context
	svcCtx *svc.ServiceContext
	logger *logger.ZeroLogger
}

// 获取聊天历史
func NewChatGetHistoryLogic(ctx context.Context, svcCtx *svc.ServiceContext) *ChatGetHistoryLogic {
	return &ChatGetHistoryLogic{
		ctx:    ctx,
		svcCtx: svcCtx,
		logger: svcCtx.Logger,
	}
}

func (l *ChatGetHistoryLogic) ChatGetHistory(req *types.ChatGetHistoryReq) (resp *types.ChatGetHistoryResp, err error) {
	// 设置分页参数
	page := req.Page
	if page <= 0 {
		page = 1
	}
	size := req.Size
	if size <= 0 {
		size = 20
	}

	offset := (page - 1) * size

	// 获取聊天历史
	messages, total, err := l.svcCtx.ChatMessagesModel.GetChatHistory(l.ctx, req.UserId, req.OtherId, offset, size)
	if err != nil {
		l.svcCtx.Logger.Error(fmt.Sprintf(utils.GET_HISTORY_MESSAGE_ERROR+": %v", err))
		panic(exceptions.NewBusinessError(utils.GET_HISTORY_MESSAGE_ERROR, err.Error()))
	}

	// 标记消息为已读
	if err := l.svcCtx.ChatMessagesModel.MarkChatHistoryAsRead(l.ctx, req.UserId, req.OtherId); err != nil {
		l.logger.Error(fmt.Sprintf(utils.MARK_READ_FAIL, err))
	}

	// 转换为ChatMessageItem
	messageItems := make([]types.ChatMessageItem, len(messages))
	for i, msg := range messages {
		messageItems[i] = types.ChatMessageItem{
			Id:         msg.Id,
			SenderId:   msg.SenderId,
			ReceiverId: msg.ReceiverId,
			Content:    msg.Content,
			IsRead:     1, // 已读
			CreatedAt:  msg.CreatedAt.Format("2006-01-02 15:04:05"),
		}
	}

	l.svcCtx.Logger.Info(utils.GET_CHAT_HISTORY_SUCCESS)

	resp = &types.ChatGetHistoryResp{
		Messages: messageItems,
		Total:    total,
	}

	return
}

// Code scaffolded by goctl. Safe to edit.
// goctl 1.9.2

package chat

import (
	"context"
	"fmt"

	"app/common/constants"
	"app/common/exceptions"
	"app/common/utils"
	"app/internal/svc"
	"app/internal/types"
	"app/model/chatMessages"

	"github.com/zeromicro/go-zero/core/mr"
)

type ChatGetHistoryLogic struct {
	ctx    context.Context
	svcCtx *svc.ServiceContext
	*utils.ZeroLogger
}

// 获取聊天历史
func NewChatGetHistoryLogic(ctx context.Context, svcCtx *svc.ServiceContext) *ChatGetHistoryLogic {
	return &ChatGetHistoryLogic{
		ctx:        ctx,
		svcCtx:     svcCtx,
		ZeroLogger: svcCtx.Logger.WithContext(ctx),
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

	// 获取聊天历史与标记已读是两个独立的 MySQL 操作，并行执行降低延迟
	var messages []*chatMessages.ChatMessages
	var total int64
	var getErr, markErr error

	_ = mr.Finish(
		func() error {
			messages, total, getErr = l.svcCtx.ChatMessagesModel.GetChatHistory(l.ctx, req.UserId, req.OtherId, offset, size)
			return getErr
		},
		func() error {
			markErr = l.svcCtx.ChatMessagesModel.MarkChatHistoryAsRead(l.ctx, req.UserId, req.OtherId)
			return markErr
		},
	)

	if getErr != nil {
		l.Error(fmt.Sprintf(constants.GET_HISTORY_MESSAGE_ERROR+": %v", getErr))
		return nil, exceptions.NewInternalServerError(constants.GET_HISTORY_MESSAGE_ERROR, getErr.Error())
	}

	if markErr != nil {
		l.Error(fmt.Sprintf(constants.MARK_READ_FAIL, markErr))
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
			CreatedAt:  msg.CreatedAt.Format(constants.DateTimeFormat),
		}
	}

	l.Info(constants.GET_CHAT_HISTORY_SUCCESS)

	resp = &types.ChatGetHistoryResp{
		Messages: messageItems,
		Total:    total,
	}

	return
}

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

type ChatGetUnreadCountLogic struct {
	ctx    context.Context
	svcCtx *svc.ServiceContext
	logger *logger.ZeroLogger
}

// 获取未读消息数
func NewChatGetUnreadCountLogic(ctx context.Context, svcCtx *svc.ServiceContext) *ChatGetUnreadCountLogic {
	return &ChatGetUnreadCountLogic{
		ctx:    ctx,
		svcCtx: svcCtx,
		logger: svcCtx.Logger,
	}
}

func (l *ChatGetUnreadCountLogic) ChatGetUnreadCount(req *types.ChatGetUnreadCountReq) (resp *types.ChatGetUnreadCountResp, err error) {
	// 获取两个用户间的未读消息数
	unreadCount, err := l.svcCtx.ChatMessagesModel.GetUnreadCount(l.ctx, req.UserId, req.OtherId)
	if err != nil {
		l.svcCtx.Logger.Error(fmt.Sprintf(utils.GET_UNREAD_COUNT_ERROR+": %v", err))
		panic(exceptions.NewBusinessError(utils.GET_UNREAD_COUNT_ERROR, err.Error()))
	}

	l.svcCtx.Logger.Info(utils.GET_UNREAD_COUNT_SUCCESS)

	resp = &types.ChatGetUnreadCountResp{
		UnreadCount: unreadCount,
	}

	return
}

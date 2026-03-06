// Code scaffolded by goctl. Safe to edit.
// goctl 1.9.2

package chat

import (
	"context"

	"app/common/logger"
	"app/common/utils"
	"app/internal/svc"
	"app/internal/types"
)

type ChatGetQueueStatusLogic struct {
	ctx    context.Context
	svcCtx *svc.ServiceContext
	*logger.ZeroLogger
}

// 获取队列状态
func NewChatGetQueueStatusLogic(ctx context.Context, svcCtx *svc.ServiceContext) *ChatGetQueueStatusLogic {
	return &ChatGetQueueStatusLogic{
		ctx:        ctx,
		svcCtx:     svcCtx,
		ZeroLogger: svcCtx.Logger,
	}
}

func (l *ChatGetQueueStatusLogic) ChatGetQueueStatus() (resp *types.ChatGetQueueStatusResp, err error) {
	// 获取队列中所有用户
	users := l.svcCtx.ChatHub.GetAllUsersInQueue()

	l.Info(utils.GET_QUEUE_STATUS_SUCCESS)

	resp = &types.ChatGetQueueStatusResp{
		OnlineUsers: users,
		Count:       len(users),
	}

	return
}

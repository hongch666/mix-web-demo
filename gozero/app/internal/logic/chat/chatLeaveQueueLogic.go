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

type ChatLeaveQueueLogic struct {
	ctx    context.Context
	svcCtx *svc.ServiceContext
	*logger.ZeroLogger
}

// 离开队列
func NewChatLeaveQueueLogic(ctx context.Context, svcCtx *svc.ServiceContext) *ChatLeaveQueueLogic {
	return &ChatLeaveQueueLogic{
		ctx:        ctx,
		svcCtx:     svcCtx,
		ZeroLogger: svcCtx.Logger,
	}
}

func (l *ChatLeaveQueueLogic) ChatLeaveQueue(req *types.ChatLeaveQueueReq) (resp *types.ChatLeaveQueueResp, err error) {
	// 离开队列
	resp = &types.ChatLeaveQueueResp{
		UserId: req.UserId,
	}

	// 检查用户是否在队列中
	if l.svcCtx.ChatHub.IsUserInQueue(req.UserId) {
		l.svcCtx.ChatHub.LeaveQueue(req.UserId)
		resp.Status = utils.USER_DISCONNECTED
	} else {
		resp.Status = utils.USER_NOT_IN_QUEUE
	}

	l.Info(utils.LEAVE_QUEUE_SUCCESS)
	return
}

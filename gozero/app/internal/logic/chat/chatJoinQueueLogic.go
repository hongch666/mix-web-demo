// Code scaffolded by goctl. Safe to edit.
// goctl 1.9.2

package chat

import (
	"context"

	"app/common/hub"
	"app/common/logger"
	"app/common/utils"
	"app/internal/svc"
	"app/internal/types"
)

type ChatJoinQueueLogic struct {
	ctx    context.Context
	svcCtx *svc.ServiceContext
	*logger.ZeroLogger
}

// 加入队列
func NewChatJoinQueueLogic(ctx context.Context, svcCtx *svc.ServiceContext) *ChatJoinQueueLogic {
	return &ChatJoinQueueLogic{
		ctx:        ctx,
		svcCtx:     svcCtx,
		ZeroLogger: svcCtx.Logger,
	}
}

func (l *ChatJoinQueueLogic) ChatJoinQueue(req *types.ChatJoinQueueReq) (resp *types.ChatJoinQueueResp, err error) {
	// 手动加入队列（不建立WebSocket连接）
	resp = &types.ChatJoinQueueResp{
		UserId: req.UserId,
	}

	// 检查用户是否已经在队列中
	if l.svcCtx.ChatHub.IsUserInQueue(req.UserId) {
		resp.Status = utils.USER_ALREADY_IN_QUEUE
	} else {
		// 创建一个虚拟的客户端（没有WebSocket连接）
		client := &hub.Client{
			UserID: req.UserId,
			Conn:   nil, // 没有WebSocket连接
			Send:   make(chan []byte, 256),
		}
		l.svcCtx.ChatHub.JoinQueue(req.UserId, client)
		resp.Status = utils.USER_CONNECTED
	}

	l.Info(utils.JOIN_QUEUE_SUCCESS)
	return
}

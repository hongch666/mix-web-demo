// Code scaffolded by goctl. Safe to edit.

package chat

import (
	"context"

	"app/common/constants"
	"app/common/utils"
	"app/internal/hub"
	"app/internal/svc"
	"app/internal/types"
)

// ChatJoinQueueLogic 处理加入聊天队列接口请求的逻辑对象
type ChatJoinQueueLogic struct {
	ctx    context.Context
	svcCtx *svc.ServiceContext
	*utils.ZeroLogger
}

// 加入队列
func NewChatJoinQueueLogic(ctx context.Context, svcCtx *svc.ServiceContext) *ChatJoinQueueLogic {
	return &ChatJoinQueueLogic{
		ctx:        ctx,
		svcCtx:     svcCtx,
		ZeroLogger: svcCtx.Logger.WithContext(ctx),
	}
}

// ChatJoinQueue 处理加入聊天队列接口请求，未在队列时以无连接的虚拟客户端入队
func (l *ChatJoinQueueLogic) ChatJoinQueue(req *types.ChatJoinQueueReq) (resp *types.ChatJoinQueueResp, err error) {
	// 手动加入队列（不建立WebSocket连接）
	resp = &types.ChatJoinQueueResp{
		UserId: req.UserId,
	}

	// 检查用户是否已经在队列中
	if l.svcCtx.ChatHub.IsUserInQueue(req.UserId) {
		resp.Status = constants.USER_ALREADY_IN_QUEUE
	} else {
		// 创建一个虚拟的客户端（没有WebSocket连接）
		client := &hub.Client{
			UserID: req.UserId,
			Conn:   nil, // 没有WebSocket连接
			Send:   make(chan []byte, 256),
		}
		l.svcCtx.ChatHub.JoinQueue(req.UserId, client)
		resp.Status = constants.USER_CONNECTED
	}

	l.Info(constants.JOIN_QUEUE_SUCCESS)
	return
}

// Code scaffolded by goctl. Safe to edit.

package chat

import (
	"context"

	"app/common/constants"
	"app/common/utils"
	"app/internal/svc"
	"app/internal/types"
)

// ChatGetQueueStatusLogic 处理获取聊天队列状态接口请求的逻辑对象
type ChatGetQueueStatusLogic struct {
	ctx    context.Context
	svcCtx *svc.ServiceContext
	*utils.ZeroLogger
}

// 获取队列状态
func NewChatGetQueueStatusLogic(ctx context.Context, svcCtx *svc.ServiceContext) *ChatGetQueueStatusLogic {
	return &ChatGetQueueStatusLogic{
		ctx:        ctx,
		svcCtx:     svcCtx,
		ZeroLogger: svcCtx.Logger.WithContext(ctx),
	}
}

// ChatGetQueueStatus 处理获取聊天队列状态接口请求，返回队列中全部在线用户及人数
func (l *ChatGetQueueStatusLogic) ChatGetQueueStatus() (resp *types.ChatGetQueueStatusResp, err error) {
	// 获取队列中所有用户
	users := l.svcCtx.ChatHub.GetAllUsersInQueue()

	l.Info(constants.GET_QUEUE_STATUS_SUCCESS)

	resp = &types.ChatGetQueueStatusResp{
		OnlineUsers: users,
		Count:       len(users),
	}

	return
}

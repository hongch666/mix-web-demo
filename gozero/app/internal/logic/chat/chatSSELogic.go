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

type ChatSSELogic struct {
	ctx    context.Context
	svcCtx *svc.ServiceContext
	*logger.ZeroLogger
}

// SSE连接
func NewChatSSELogic(ctx context.Context, svcCtx *svc.ServiceContext) *ChatSSELogic {
	return &ChatSSELogic{
		ctx:        ctx,
		svcCtx:     svcCtx,
		ZeroLogger: svcCtx.Logger,
	}
}

func (l *ChatSSELogic) ChatSSE(req *types.ChatSSEConnectReq) (resp *types.ChatSSEConnectResp, err error) {
	// SSE实时推送实现
	l.Info(utils.SSE_CONNECTION_ESTABLISHED_MESSAGE)

	return
}

// Code scaffolded by goctl. Safe to edit.
// goctl 1.9.2

package chat

import (
	"context"

	"app/common/utils"
	"app/internal/svc"
	"app/internal/types"
)

type ChatSSELogic struct {
	ctx    context.Context
	svcCtx *svc.ServiceContext
	*utils.ZeroLogger
}

// SSE连接
func NewChatSSELogic(ctx context.Context, svcCtx *svc.ServiceContext) *ChatSSELogic {
	return &ChatSSELogic{
		ctx:        ctx,
		svcCtx:     svcCtx,
		ZeroLogger: svcCtx.Logger.WithContext(ctx),
	}
}

func (l *ChatSSELogic) ChatSSE(req *types.ChatSSEConnectReq) (resp *types.ChatSSEConnectResp, err error) {
	// SSE实时推送实现
	l.Info(utils.SSE_CONNECTION_ESTABLISHED_MESSAGE)

	return
}

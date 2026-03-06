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
}

// SSE连接
func NewChatSSELogic(ctx context.Context, svcCtx *svc.ServiceContext) *ChatSSELogic {
	return &ChatSSELogic{
		ctx:    ctx,
		svcCtx: svcCtx,
	}
}

func (l *ChatSSELogic) ChatSSE(req *types.ChatSSEConnectReq) (resp *types.ChatSSEConnectResp, err error) {
	// SSE实时推送实现
	l.svcCtx.Logger.Info(utils.SSE_CONNECTION_ESTABLISHED_MESSAGE)

	return
}

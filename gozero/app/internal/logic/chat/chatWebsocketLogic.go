// Code scaffolded by goctl. Safe to edit.
// goctl 1.9.2

package chat

import (
	"context"

	"app/common/utils"
	"app/internal/svc"
	"app/internal/types"
)

type ChatWebsocketLogic struct {
	ctx    context.Context
	svcCtx *svc.ServiceContext
}

// WebSocket连接
func NewChatWebsocketLogic(ctx context.Context, svcCtx *svc.ServiceContext) *ChatWebsocketLogic {
	return &ChatWebsocketLogic{
		ctx:    ctx,
		svcCtx: svcCtx,
	}
}

func (l *ChatWebsocketLogic) ChatWebsocket(req *types.ChatWsConnectReq) (resp *types.ChatWsConnectResp, err error) {
	// WebSocket实时瘪天实现
	l.svcCtx.Logger.Info(utils.WEBSOCKET_CONNECTION_ESTABLISHED_MESSAGE)

	return
}

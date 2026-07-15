// Code scaffolded by goctl. Safe to edit.
// goctl 1.9.2

package chat

import (
	"context"

	"app/common/constants"
	"app/common/utils"
	"app/internal/svc"
	"app/internal/types"
)

type ChatWebsocketLogic struct {
	ctx    context.Context
	svcCtx *svc.ServiceContext
	*utils.ZeroLogger
}

// WebSocket连接
func NewChatWebsocketLogic(ctx context.Context, svcCtx *svc.ServiceContext) *ChatWebsocketLogic {
	return &ChatWebsocketLogic{
		ctx:        ctx,
		svcCtx:     svcCtx,
		ZeroLogger: svcCtx.Logger.WithContext(ctx),
	}
}

func (l *ChatWebsocketLogic) ChatWebsocket(req *types.ChatWsConnectReq) (resp *types.ChatWsConnectResp, err error) {
	// WebSocket实时瘪天实现
	l.Info(constants.WEBSOCKET_CONNECTION_ESTABLISHED_MESSAGE)

	return
}

// Code scaffolded by goctl. Safe to edit.

package chat

import (
	"net/http"

	"app/common/constants"
	"app/common/utils"
	"app/internal/logic/chat"
	"app/internal/middleware"
	"app/internal/svc"
	"app/internal/types"

	"github.com/gorilla/websocket"
	"github.com/zeromicro/go-zero/rest/httpx"
)

var upgrader = websocket.Upgrader{
	CheckOrigin: func(r *http.Request) bool {
		return true
	},
}

// WebSocket连接
func ChatWebsocketHandler(svcCtx *svc.ServiceContext) http.HandlerFunc {
	return middleware.ApplyApiLog(svcCtx.RabbitMQPublisher, svcCtx.Logger, func(w http.ResponseWriter, r *http.Request) {
		var req types.ChatWsConnectReq
		if err := httpx.Parse(r, &req); err != nil {
			utils.HandleErrorWithCode(w, err, constants.HttpBadRequest)
			return
		}

		l := chat.NewChatWebsocketLogic(r.Context(), svcCtx)
		userID, err := l.ResolveUserID(&req, r.Header.Get(constants.HeaderUserID))
		if err != nil {
			utils.HandleError(w, err)
			return
		}

		conn, err := upgrader.Upgrade(w, r, nil)
		if err != nil {
			// 用带请求上下文的 logger，避免与根 logger（context.Background）一样丢失 trace_id
			l.Error(constants.WS_CONNECT_FAIL + err.Error())
			return
		}

		l.Info(constants.WEBSOCKET_CONNECTION_ESTABLISHED_MESSAGE)

		svcCtx.ChatHub.HandleWebSocketConnection(r.Context(), conn, userID)
	}, constants.API_LOG_WEBSOCKET_CONNECTION)
}

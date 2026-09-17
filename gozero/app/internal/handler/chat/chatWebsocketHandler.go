// Code scaffolded by goctl. Safe to edit.
// goctl 1.9.2

package chat

import (
	"net/http"

	"app/common/constants"
	"app/common/utils"
	"app/internal/hub"
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
			utils.Error(w, constants.HttpBadRequest, err.Error())
			return
		}

		if err := req.Validate(); err != nil {
			utils.HandleError(w, err)
			return
		}

		l := chat.NewChatWebsocketLogic(r.Context(), svcCtx)
		userID, err := l.ResolveUserID(&req, r.Header.Get("X-User-Id"))
		if err != nil {
			utils.HandleError(w, err)
			return
		}

		conn, err := upgrader.Upgrade(w, r, nil)
		if err != nil {
			svcCtx.Logger.Error(constants.WS_CONNECT_FAIL + err.Error())
			return
		}

		svcCtx.Logger.Info(constants.WEBSOCKET_CONNECTION_ESTABLISHED_MESSAGE)

		// 创建新的客户端并加入队列
		client := &hub.Client{
			UserID:       userID,
			ConnectionID: hub.NewConnectionID("ws"),
			Conn:         conn,
			Send:         make(chan []byte, constants.WebSocketSendBufferSize),
			MarkRead:     svcCtx.ChatMessagesModel.MarkChatHistoryAsReadThrough,
		}
		svcCtx.ChatHub.JoinQueue(userID, client)

		// 启动读写协程，这里使用带 recover 的安全封装，避免子 goroutine panic 直接影响整个进程
		utils.SafeGo(svcCtx.Logger, "websocket_write_pump", func() {
			client.WritePump()
		})
		utils.SafeGo(svcCtx.Logger, "websocket_read_pump", func() {
			client.ReadPump()
		})
	}, constants.API_LOG_WEBSOCKET_CONNECTION)
}

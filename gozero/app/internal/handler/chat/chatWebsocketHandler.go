// Code scaffolded by goctl. Safe to edit.
// goctl 1.9.2

package chat

import (
	"net/http"

	"app/common/hub"
	"app/common/utils"
	"app/internal/middleware"
	"app/internal/svc"

	"github.com/gorilla/websocket"
)

var upgrader = websocket.Upgrader{
	CheckOrigin: func(r *http.Request) bool {
		return true
	},
}

// WebSocket连接
func ChatWebsocketHandler(svcCtx *svc.ServiceContext) http.HandlerFunc {
	return middleware.ApplyApiLog(svcCtx.RabbitMQChannel, svcCtx.Logger, func(w http.ResponseWriter, r *http.Request) {
		userID := r.URL.Query().Get("userId")
		if userID == "" {
			// 尝试从Header获取（网关传递的用户信息）
			userID = r.Header.Get("X-User-Id")
		}

		if userID == "" {
			svcCtx.Logger.Error(utils.USER_ID_LESS)
			utils.Error(w, utils.USER_ID_LESS)
			return
		}

		conn, err := upgrader.Upgrade(w, r, nil)
		if err != nil {
			svcCtx.Logger.Error(utils.WS_CONNECT_FAIL + err.Error())
			return
		}

		// 检查用户是否已经在队列中
		if existingClient, exists := svcCtx.ChatHub.GetUserFromQueue(userID); exists {
			// 用户已在队列中，更新其WebSocket连接
			existingClient.Conn = conn
			existingClient.Send = make(chan []byte, 256)
		} else {
			// 创建新的客户端并加入队列
			client := &hub.Client{
				UserID: userID,
				Conn:   conn,
				Send:   make(chan []byte, 256),
			}
			svcCtx.ChatHub.JoinQueue(userID, client)
		}

		// 获取更新后的客户端
		client, _ := svcCtx.ChatHub.GetUserFromQueue(userID)

		// 启动读写协程
		go client.WritePump()
		go client.ReadPump()
	}, "WebSocket连接")
}

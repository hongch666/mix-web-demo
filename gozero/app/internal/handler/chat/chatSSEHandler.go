// Code scaffolded by goctl. Safe to edit.
// goctl 1.9.2

package chat

import (
	"io"
	"net/http"
	"time"

	"app/common/chat"
	"app/common/utils"
	"app/dto"
	"app/internal/middleware"
	"app/internal/svc"
)

// @Summary 		SSE连接
// @Description 	建立SSE连接用于接收实时消息推送（长连接，需通过WebSocket客户端连接）
// @Tags 			chat
// @Accept  		json
// @Produce 		text/event-stream
// @Param   		userId query string true "用户ID"
// @Success 		200 {string} string "消息流"
// @Failure 		400 {object} map[string]interface{} "缺少用户ID"
// @Failure 		500 {object} map[string]interface{} "服务器错误"
// @Router  		/sse/chat [get]
// SSE连接
func ChatSSEHandler(svcCtx *svc.ServiceContext) http.HandlerFunc {
	return middleware.ApplyApiLog(svcCtx.RabbitMQChannel, svcCtx.Logger, func(w http.ResponseWriter, r *http.Request) {
		userID := r.URL.Query().Get("userId")
		if userID == "" {
			// 尝试从Header获取（网关传递的用户信息）
			userID = r.Header.Get("X-User-Id")
		}

		if userID == "" {
			svcCtx.Logger.Error(utils.USER_ID_LESS)
			utils.Error(w, http.StatusBadRequest, utils.USER_ID_LESS)
			return
		}

		// 设置SSE响应头
		w.Header().Set("Content-Type", "text/event-stream")
		w.Header().Set("Cache-Control", "no-cache")
		w.Header().Set("Connection", "keep-alive")

		sendCh := make(chan any, 256)
		closeCh := make(chan bool)

		// 注册客户端
		svcCtx.SSEHub.RegisterClient(userID, sendCh, closeCh)
		defer svcCtx.SSEHub.UnregisterClient(userID)

		// 发送初始化连接消息
		initMessage := &dto.SSEMessageNotification{
			Type:         "connected",
			UserID:       userID,
			UnreadCounts: make(map[string]int64),
		}
		sseMessage := chat.FormatSSEMessage(initMessage)
		_, _ = io.WriteString(w, sseMessage)
		if f, ok := w.(http.Flusher); ok {
			f.Flush()
		}

		// 创建心跳定时器
		ticker := time.NewTicker(30 * time.Second)
		defer ticker.Stop()

		// 响应流
		for {
			select {
			case <-closeCh:
				return
			case <-ticker.C:
				// 发送心跳消息
				heartbeat := utils.SSE_HEARTBEAT
				_, err := io.WriteString(w, heartbeat)
				if err != nil {
					svcCtx.Logger.Error(utils.SSE_HEARTBEAT_WRITE_FAIL + err.Error())
					return
				}
				if f, ok := w.(http.Flusher); ok {
					f.Flush()
				}
			case notification := <-sendCh:
				// 发送SSE格式的消息
				sseMessage := chat.FormatSSEMessage(notification)
				// 如果格式化后消息为空,跳过此次发送
				if sseMessage == "" {
					svcCtx.Logger.Warning(utils.EMPTY_SSE)
					continue
				}
				_, err := io.WriteString(w, sseMessage)
				if err != nil {
					svcCtx.Logger.Error(utils.SSE_WRITE_FAIL + err.Error())
					return
				}
				if f, ok := w.(http.Flusher); ok {
					f.Flush()
				}
			}
		}
	}, "SSE连接")
}

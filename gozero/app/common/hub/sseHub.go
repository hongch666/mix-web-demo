package hub

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"sync"
	"time"

	"app/common/constants"
	"app/common/utils"
)

// SSE客户端
type SSEClient struct {
	UserID       string
	ConnectionID string
	SendCh       chan any
	CloseCh      chan bool
}

// SSE中心管理
type SSEHubManager struct {
	clients map[string]map[string]*SSEClient // userID -> connectionID -> SSEClient
	mu      sync.RWMutex
	*utils.ZeroLogger
}

var (
	sseHubInstance *SSEHubManager
	once           sync.Once
)

// GetSSEHub 获取SSE中心实例
func GetSSEHub() *SSEHubManager {
	once.Do(func() {
		sseHubInstance = &SSEHubManager{
			clients: make(map[string]map[string]*SSEClient),
		}
	})
	return sseHubInstance
}

// RegisterClient 注册SSE客户端
func (hub *SSEHubManager) RegisterClient(userID string, connectionID string, sendCh chan any, closeCh chan bool) {
	if connectionID == "" {
		return
	}

	hub.mu.Lock()
	defer hub.mu.Unlock()

	if _, ok := hub.clients[userID]; !ok {
		hub.clients[userID] = make(map[string]*SSEClient)
	}

	hub.clients[userID][connectionID] = &SSEClient{
		UserID:       userID,
		ConnectionID: connectionID,
		SendCh:       sendCh,
		CloseCh:      closeCh,
	}
	if hub.ZeroLogger != nil {
		hub.Info(constants.SSE_REGISTER_SUCCESS_MESSAGE)
	}
}

// UnregisterClient 注销SSE客户端
// 通过 connectionID 进行身份校验，防止旧连接的 defer 误关闭新连接
func (hub *SSEHubManager) UnregisterClient(userID string, connectionID string) {
	if connectionID == "" {
		return
	}

	hub.mu.Lock()
	defer hub.mu.Unlock()

	clients, ok := hub.clients[userID]
	if ok {
		if _, exists := clients[connectionID]; !exists {
			return
		}
		delete(clients, connectionID)
		if len(clients) == 0 {
			delete(hub.clients, userID)
		}
		if hub.ZeroLogger != nil {
			hub.Info(constants.SSE_UNREGISTER_SUCCESS_MESSAGE)
		}
	}
}

// SendNotificationToUser 发送通知给特定用户
func (hub *SSEHubManager) SendNotificationToUser(userID string, notification *SSEMessageNotification) {
	if notification == nil {
		if hub.ZeroLogger != nil {
			hub.Warning(constants.SSE_SEND_EMPTY_WARNING_MESSAGE)
		}
		return
	}

	hub.mu.RLock()
	clients, ok := hub.clients[userID]
	hub.mu.RUnlock()

	if !ok || len(clients) == 0 {
		if hub.ZeroLogger != nil {
			hub.Warning(constants.SSE_CLIENT_NOT_FOUND_WARNING_MESSAGE)
		}
		return
	}

	var sentAny bool
	for _, client := range clients {
		if client == nil {
			continue
		}

		select {
		case client.SendCh <- notification:
			sentAny = true
		default:
			if hub.ZeroLogger != nil {
				hub.Warning(constants.SSE_SEND_FAIL_WARNING_MESSAGE)
			}
		}
	}

	if sentAny && hub.ZeroLogger != nil {
		hub.Info(constants.SSE_SEND_SUCCESS_MESSAGE)
	}
}

// BroadcastNotification 广播通知给所有客户端
func (hub *SSEHubManager) BroadcastNotification(notification any) {
	hub.mu.RLock()
	defer hub.mu.RUnlock()

	for _, userClients := range hub.clients {
		for _, client := range userClients {
			if client == nil {
				continue
			}

			select {
			case client.SendCh <- notification:
				if hub.ZeroLogger != nil {
					hub.Debug(constants.SSE_BROADCAST_SUCCESS_MESSAGE)
				}
			default:
				if hub.ZeroLogger != nil {
					hub.Warning(constants.SSE_BROADCAST_FAIL_WARNING_MESSAGE)
				}
			}
		}
	}
}

// HandleConnection 处理 SSE 连接的完整生命周期
// 包括：注册客户端、发送初始化消息、事件循环（心跳+消息分发）
// Handler 层只需调用此方法，无需关心 SSE 协议细节
func (hub *SSEHubManager) HandleConnection(w http.ResponseWriter, r *http.Request, userID string) {
	// 设置SSE响应头
	w.Header().Set("Content-Type", "text/event-stream")
	w.Header().Set("Cache-Control", "no-cache")
	w.Header().Set("Connection", "keep-alive")

	connectionID := NewConnectionID("sse")
	sendCh := make(chan any, 256)
	closeCh := make(chan bool)

	// 注册客户端
	hub.RegisterClient(userID, connectionID, sendCh, closeCh)
	// 传入 connectionID 作为身份标识，防止旧连接的 defer 误关闭新连接
	defer hub.UnregisterClient(userID, connectionID)

	// 发送初始化连接消息
	initMessage := &SSEMessageNotification{
		Type:         "connected",
		UserID:       userID,
		UnreadCounts: make(map[string]int64),
	}
	sseMessage := FormatSSEMessage(initMessage)
	_, _ = io.WriteString(w, sseMessage)
	if f, ok := w.(http.Flusher); ok {
		f.Flush()
	}

	// 创建心跳定时器
	ticker := time.NewTicker(30 * time.Second)
	defer ticker.Stop()

	// 事件循环
	for {
		select {
		case <-r.Context().Done():
			// 客户端主动断开连接
			return
		case <-closeCh:
			return
		case <-ticker.C:
			// 发送心跳消息
			heartbeat := constants.SSE_HEARTBEAT
			_, err := io.WriteString(w, heartbeat)
			if err != nil {
				if hub.ZeroLogger != nil {
					hub.Error(constants.SSE_HEARTBEAT_WRITE_FAIL + err.Error())
				}
				return
			}
			if f, ok := w.(http.Flusher); ok {
				f.Flush()
			}
		case notification := <-sendCh:
			// 发送SSE格式的消息
			sseMessage := FormatSSEMessage(notification)
			// 如果格式化后消息为空,跳过此次发送
			if sseMessage == "" {
				if hub.ZeroLogger != nil {
					hub.Warning(constants.EMPTY_SSE)
				}
				continue
			}
			_, err := io.WriteString(w, sseMessage)
			if err != nil {
				if hub.ZeroLogger != nil {
					hub.Error(constants.SSE_WRITE_FAIL + err.Error())
				}
				return
			}
			if f, ok := w.(http.Flusher); ok {
				f.Flush()
			}
		}
	}
}

// FormatSSEMessage 格式化SSE消息
func FormatSSEMessage(data any) string {
	if data == nil {
		if sseHubInstance != nil && sseHubInstance.ZeroLogger != nil {
			sseHubInstance.Warning(constants.SSE_SEND_EMPTY_MESSAGE_WARNING_MESSAGE)
		}
		return ""
	}

	jsonData, err := json.Marshal(data)
	if err != nil {
		if sseHubInstance != nil && sseHubInstance.ZeroLogger != nil {
			sseHubInstance.Error(constants.SSE_SERIALIZE_MESSAGE_ERROR_MESSAGE)
		}
		return ""
	}

	// 检查是否为null
	if string(jsonData) == "null" {
		if sseHubInstance != nil && sseHubInstance.ZeroLogger != nil {
			sseHubInstance.Warning(constants.SSE_SERIALIZE_MESSAGE_EMPTY)
		}
		return ""
	}

	return fmt.Sprintf("data: %s\n\n", string(jsonData))
}

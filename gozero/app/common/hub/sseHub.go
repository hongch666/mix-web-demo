package hub

import (
	"encoding/json"
	"fmt"
	"sync"

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
		hub.Info(utils.SSE_REGISTER_SUCCESS_MESSAGE)
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
			hub.Info(utils.SSE_UNREGISTER_SUCCESS_MESSAGE)
		}
	}
}

// SendNotificationToUser 发送通知给特定用户
func (hub *SSEHubManager) SendNotificationToUser(userID string, notification *SSEMessageNotification) {
	if notification == nil {
		if hub.ZeroLogger != nil {
			hub.Warning(utils.SSE_SEND_EMPTY_WARNING_MESSAGE)
		}
		return
	}

	hub.mu.RLock()
	clients, ok := hub.clients[userID]
	hub.mu.RUnlock()

	if !ok || len(clients) == 0 {
		if hub.ZeroLogger != nil {
			hub.Warning(utils.SSE_CLIENT_NOT_FOUND_WARNING_MESSAGE)
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
				hub.Warning(utils.SSE_SEND_FAIL_WARNING_MESSAGE)
			}
		}
	}

	if sentAny && hub.ZeroLogger != nil {
		hub.Info(utils.SSE_SEND_SUCCESS_MESSAGE)
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
					hub.Debug(utils.SSE_BROADCAST_SUCCESS_MESSAGE)
				}
			default:
				if hub.ZeroLogger != nil {
					hub.Warning(utils.SSE_BROADCAST_FAIL_WARNING_MESSAGE)
				}
			}
		}
	}
}

// FormatSSEMessage 格式化SSE消息
func FormatSSEMessage(data any) string {
	if data == nil {
		if sseHubInstance != nil && sseHubInstance.ZeroLogger != nil {
			sseHubInstance.Warning(utils.SSE_SEND_EMPTY_MESSAGE_WARNING_MESSAGE)
		}
		return ""
	}

	jsonData, err := json.Marshal(data)
	if err != nil {
		if sseHubInstance != nil && sseHubInstance.ZeroLogger != nil {
			sseHubInstance.Error(utils.SSE_SERIALIZE_MESSAGE_ERROR_MESSAGE)
		}
		return ""
	}

	// 检查是否为null
	if string(jsonData) == "null" {
		if sseHubInstance != nil && sseHubInstance.ZeroLogger != nil {
			sseHubInstance.Warning(utils.SSE_SERIALIZE_MESSAGE_EMPTY)
		}
		return ""
	}

	return fmt.Sprintf("data: %s\n\n", string(jsonData))
}

package chat

import (
	"encoding/json"
	"fmt"
	"sync"

	"app/common/logger"
	"app/common/utils"
	"app/dto"
)

// SSE客户端
type SSEClient struct {
	UserID  string
	SendCh  chan any
	CloseCh chan bool
}

// SSE中心管理
type SSEHubManager struct {
	clients map[string]*SSEClient // userID -> SSEClient
	mu      sync.RWMutex
	*logger.ZeroLogger
}

var sseHubInstance *SSEHubManager
var once sync.Once

// GetSSEHub 获取SSE中心实例
func GetSSEHub() *SSEHubManager {
	once.Do(func() {
		sseHubInstance = &SSEHubManager{
			clients: make(map[string]*SSEClient),
		}
	})
	return sseHubInstance
}

// RegisterClient 注册SSE客户端
func (hub *SSEHubManager) RegisterClient(userID string, sendCh chan any, closeCh chan bool) {
	hub.mu.Lock()
	defer hub.mu.Unlock()

	// 如果用户已存在，关闭旧连接
	if existing, ok := hub.clients[userID]; ok {
		close(existing.SendCh)
		close(existing.CloseCh)
	}

	hub.clients[userID] = &SSEClient{
		UserID:  userID,
		SendCh:  sendCh,
		CloseCh: closeCh,
	}
	if hub.ZeroLogger != nil {
		hub.Info(utils.SSE_REGISTER_SUCCESS_MESSAGE)
	}
}

// UnregisterClient 注销SSE客户端
func (hub *SSEHubManager) UnregisterClient(userID string) {
	hub.mu.Lock()
	defer hub.mu.Unlock()

	if client, ok := hub.clients[userID]; ok {
		close(client.SendCh)
		close(client.CloseCh)
		delete(hub.clients, userID)
		if hub.ZeroLogger != nil {
			hub.Info(utils.SSE_UNREGISTER_SUCCESS_MESSAGE)
		}
	}
}

// SendNotificationToUser 发送通知给特定用户
func (hub *SSEHubManager) SendNotificationToUser(userID string, notification *dto.SSEMessageNotification) {
	if notification == nil {
		if hub.ZeroLogger != nil {
			hub.Warning(utils.SSE_SEND_EMPTY_WARNING_MESSAGE)
		}
		return
	}

	hub.mu.RLock()
	client, ok := hub.clients[userID]
	hub.mu.RUnlock()

	if !ok {
		if hub.ZeroLogger != nil {
			hub.Warning(utils.SSE_CLIENT_NOT_FOUND_WARNING_MESSAGE)
		}
		return
	}

	select {
	case client.SendCh <- notification:
		if hub.ZeroLogger != nil {
			hub.Info(utils.SSE_SEND_SUCCESS_MESSAGE)
		}
	default:
		if hub.ZeroLogger != nil {
			hub.Warning(utils.SSE_SEND_FAIL_WARNING_MESSAGE)
		}
	}
}

// BroadcastNotification 广播通知给所有客户端
func (hub *SSEHubManager) BroadcastNotification(notification any) {
	hub.mu.RLock()
	defer hub.mu.RUnlock()

	for _, client := range hub.clients {
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

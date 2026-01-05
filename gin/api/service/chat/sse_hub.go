package chat

import (
	"encoding/json"
	"fmt"
	"gin_proj/common/utils"
	"gin_proj/entity/dto"
	"sync"
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
	utils.FileLogger.Info(fmt.Sprintf("SSE客户端 %s 已注册", userID))
}

// UnregisterClient 注销SSE客户端
func (hub *SSEHubManager) UnregisterClient(userID string) {
	hub.mu.Lock()
	defer hub.mu.Unlock()

	if client, ok := hub.clients[userID]; ok {
		close(client.SendCh)
		close(client.CloseCh)
		delete(hub.clients, userID)
		utils.FileLogger.Info(fmt.Sprintf("SSE客户端 %s 已注销", userID))
	}
}

// SendNotificationToUser 发送通知给特定用户
func (hub *SSEHubManager) SendNotificationToUser(userID string, notification *dto.SSEMessageNotification) {
	if notification == nil {
		utils.FileLogger.Warning(fmt.Sprintf("尝试发送空通知给用户 %s", userID))
		return
	}

	hub.mu.RLock()
	client, ok := hub.clients[userID]
	hub.mu.RUnlock()

	if !ok {
		utils.FileLogger.Warning(fmt.Sprintf("用户 %s 的SSE客户端未找到", userID))
		return
	}

	select {
	case client.SendCh <- notification:
		utils.FileLogger.Info(fmt.Sprintf("SSE通知已发送给用户 %s", userID))
	default:
		utils.FileLogger.Warning(fmt.Sprintf("无法发送SSE通知给用户 %s,通道已满", userID))
	}
}

// BroadcastNotification 广播通知给所有客户端
func (hub *SSEHubManager) BroadcastNotification(notification any) {
	hub.mu.RLock()
	defer hub.mu.RUnlock()

	for userID, client := range hub.clients {
		select {
		case client.SendCh <- notification:
			utils.FileLogger.Debug(fmt.Sprintf("广播消息已发送给用户 %s", userID))
		default:
			utils.FileLogger.Warning(fmt.Sprintf("无法广播消息给用户 %s，通道已满", userID))
		}
	}
}

// FormatSSEMessage 格式化SSE消息
func FormatSSEMessage(data any) string {
	if data == nil {
		utils.FileLogger.Warning("尝试发送空的SSE消息")
		return ""
	}

	jsonData, err := json.Marshal(data)
	if err != nil {
		utils.FileLogger.Error(fmt.Sprintf("序列化SSE消息失败: %v", err))
		return ""
	}

	// 检查是否为null
	if string(jsonData) == "null" {
		utils.FileLogger.Warning("序列化后的SSE消息为null")
		return ""
	}

	return fmt.Sprintf("data: %s\n\n", string(jsonData))
}

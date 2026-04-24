package hub

import (
	"context"
	"encoding/json"
	"fmt"
	"strconv"
	"sync"
	"sync/atomic"
	"time"

	"app/common/utils"

	"github.com/gorilla/websocket"
)

// WebSocket客户端
type Client struct {
	UserID       string
	ConnectionID string
	Conn         *websocket.Conn
	Send         chan []byte
	closeOnce    sync.Once
	*utils.ZeroLogger
}

// 全局聊天队列管理
var (
	chatQueue = &ChatQueue{
		clients: make(map[string]map[string]*Client),
		mu:      sync.RWMutex{},
	}
	chatConnectionSeq atomic.Uint64
)

type ChatQueue struct {
	clients map[string]map[string]*Client // userID -> connectionID -> client
	mu      sync.RWMutex
}

type ChatHub struct {
	ctx context.Context
	*utils.ZeroLogger
}

// NewConnectionID 生成连接标识
func NewConnectionID(prefix string) string {
	return prefix + "-" + strconv.FormatInt(time.Now().UnixNano(), 10) + "-" + strconv.FormatUint(chatConnectionSeq.Add(1), 10)
}

// 加入队列
func (s *ChatHub) JoinQueue(userID string, client *Client) {
	if client == nil {
		return
	}
	if client.ConnectionID == "" {
		client.ConnectionID = NewConnectionID("ws")
	}

	chatQueue.mu.Lock()
	if _, ok := chatQueue.clients[userID]; !ok {
		chatQueue.clients[userID] = make(map[string]*Client)
	}
	chatQueue.clients[userID][client.ConnectionID] = client
	chatQueue.mu.Unlock()
	if s.ZeroLogger != nil {
		client.ZeroLogger = s.ZeroLogger
	}
	if s.ZeroLogger != nil {
		s.Info(utils.USER_JOINED_QUEUE_MESSAGE)
	}
}

// 离开队列
func (s *ChatHub) LeaveQueue(userID string) {
	chatQueue.mu.Lock()
	if clients, ok := chatQueue.clients[userID]; ok {
		delete(chatQueue.clients, userID)
		for _, client := range clients {
			client.Shutdown()
		}
	}
	chatQueue.mu.Unlock()
	if s.ZeroLogger != nil {
		s.Info(utils.USER_LEFT_QUEUE_MESSAGE)
	}
}

// LeaveQueueIfMatch 仅当当前队列中的 client 与传入实例一致时才移除，避免旧连接退出时误删新连接
func (s *ChatHub) LeaveQueueIfMatch(userID string, connectionID string, client *Client) {
	if client == nil || connectionID == "" {
		return
	}

	chatQueue.mu.Lock()
	currentClients, ok := chatQueue.clients[userID]
	currentClient, exists := currentClients[connectionID]
	if ok && exists && currentClient == client {
		client.Shutdown()
		delete(currentClients, connectionID)
		if len(currentClients) == 0 {
			delete(chatQueue.clients, userID)
		}
	}
	chatQueue.mu.Unlock()
	if ok && exists && currentClient == client && s.ZeroLogger != nil {
		s.Info(utils.USER_LEFT_QUEUE_MESSAGE)
	}
}

// 检查用户是否在队列中
func (s *ChatHub) IsUserInQueue(userID string) bool {
	chatQueue.mu.RLock()
	clients, exists := chatQueue.clients[userID]
	userExists := exists && len(clients) > 0
	chatQueue.mu.RUnlock()
	return userExists
}

// 获取队列中的用户
func (s *ChatHub) GetUserFromQueue(userID string) (*Client, bool) {
	chatQueue.mu.RLock()
	clients, exists := chatQueue.clients[userID]
	var client *Client
	if exists {
		for _, item := range clients {
			client = item
			break
		}
	}
	chatQueue.mu.RUnlock()
	return client, client != nil
}

// GetUserClients 获取指定用户的全部连接副本
func (s *ChatHub) GetUserClients(userID string) []*Client {
	chatQueue.mu.RLock()
	defer chatQueue.mu.RUnlock()

	clients, exists := chatQueue.clients[userID]
	if !exists || len(clients) == 0 {
		return nil
	}

	result := make([]*Client, 0, len(clients))
	for _, client := range clients {
		result = append(result, client)
	}
	return result
}

// 向队列中的用户发送消息
func (s *ChatHub) SendMessageToQueue(userID string, message []byte) bool {
	clients := s.GetUserClients(userID)
	if len(clients) == 0 {
		return false
	}

	sentAny := false
	failedClients := make([]*Client, 0)
	for _, client := range clients {
		if client == nil {
			continue
		}
		if client.Conn == nil {
			continue
		}

		if client.SafeSend(message) {
			sentAny = true
			continue
		}
		failedClients = append(failedClients, client)
	}

	for _, client := range failedClients {
		s.LeaveQueueIfMatch(userID, client.ConnectionID, client)
	}

	if !sentAny && s.ZeroLogger != nil {
		s.Warning(utils.USER_IN_QUEUE_NOT_CONNECTED_WARNING)
	}

	return sentAny
}

// 获取队列中所有用户
func (s *ChatHub) GetAllUsersInQueue() []string {
	chatQueue.mu.RLock()
	defer chatQueue.mu.RUnlock()

	users := make([]string, 0, len(chatQueue.clients))
	for userID := range chatQueue.clients {
		users = append(users, userID)
	}
	return users
}

// Shutdown 安全关闭客户端资源，允许重复调用
func (c *Client) Shutdown() {
	if c == nil {
		return
	}

	c.closeOnce.Do(func() {
		if c.Conn != nil {
			_ = c.Conn.Close()
		}
		if c.Send != nil {
			close(c.Send)
		}
	})
}

// SafeSend 向客户端发送消息；如果连接已关闭或 channel 已关闭，返回 false 而不是 panic
func (c *Client) SafeSend(message []byte) (ok bool) {
	defer func() {
		if recover() != nil {
			ok = false
		}
	}()

	select {
	case c.Send <- message:
		return true
	default:
		return false
	}
}

func (c *Client) ReadPump() {
	defer func() {
		chatHub := &ChatHub{ZeroLogger: c.ZeroLogger}
		chatHub.LeaveQueueIfMatch(c.UserID, c.ConnectionID, c)
	}()

	c.Conn.SetReadLimit(512)
	for {
		_, messageBytes, err := c.Conn.ReadMessage()
		if err != nil {
			if websocket.IsUnexpectedCloseError(err, websocket.CloseGoingAway, websocket.CloseAbnormalClosure) {
				if c.ZeroLogger != nil {
					c.Error(fmt.Sprintf(utils.WS_ERROR, err))
				}
			}
			break
		}

		// 解析消息
		var wsMessage WebSocketMessage
		if err := json.Unmarshal(messageBytes, &wsMessage); err != nil {
			if c.ZeroLogger != nil {
				c.Error(fmt.Sprintf(utils.PARSE_MESSAGE_FAIL, err))
			}
			continue
		}

		// 处理ping消息
		if wsMessage.Type == utils.HEARTBEAT_MESSAGE {
			pongMessage := WebSocketMessage{Type: utils.HEARTBEAT_RESPONSE}
			pongBytes, _ := json.Marshal(pongMessage)
			if !c.SafeSend(pongBytes) {
				return
			}
		}
	}
}

func (c *Client) WritePump() {
	defer c.Shutdown()

	for message := range c.Send {
		if err := c.Conn.WriteMessage(websocket.TextMessage, message); err != nil {
			if c.ZeroLogger != nil {
				c.Error(fmt.Sprintf("WebSocket 写消息失败: %v", err))
			}
			break
		}
	}
	_ = c.Conn.WriteMessage(websocket.CloseMessage, []byte{})
}

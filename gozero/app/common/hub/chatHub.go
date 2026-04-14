package hub

import (
	"context"
	"encoding/json"
	"fmt"
	"sync"

	"app/common/logger"
	"app/common/utils"

	"github.com/gorilla/websocket"
)

// WebSocket客户端
type Client struct {
	UserID    string
	Conn      *websocket.Conn
	Send      chan []byte
	closeOnce sync.Once
	*logger.ZeroLogger
}

// 全局聊天队列管理
var (
	chatQueue = &ChatQueue{
		clients: make(map[string]*Client),
		mu:      sync.RWMutex{},
	}
)

type ChatQueue struct {
	clients map[string]*Client // userID -> client
	mu      sync.RWMutex
}

type ChatHub struct {
	ctx context.Context
	*logger.ZeroLogger
}

// 加入队列
func (s *ChatHub) JoinQueue(userID string, client *Client) {
	chatQueue.mu.Lock()
	chatQueue.clients[userID] = client
	chatQueue.mu.Unlock()
	if client != nil && s.ZeroLogger != nil {
		client.ZeroLogger = s.ZeroLogger
	}
	if s.ZeroLogger != nil {
		s.Info(utils.USER_JOINED_QUEUE_MESSAGE)
	}
}

// 离开队列
func (s *ChatHub) LeaveQueue(userID string) {
	chatQueue.mu.Lock()
	if client, ok := chatQueue.clients[userID]; ok {
		client.Shutdown()
		delete(chatQueue.clients, userID)
	}
	chatQueue.mu.Unlock()
	if s.ZeroLogger != nil {
		s.Info(utils.USER_LEFT_QUEUE_MESSAGE)
	}
}

// LeaveQueueIfMatch 仅当当前队列中的 client 与传入实例一致时才移除，避免旧连接退出时误删新连接
func (s *ChatHub) LeaveQueueIfMatch(userID string, client *Client) {
	chatQueue.mu.Lock()
	currentClient, ok := chatQueue.clients[userID]
	if ok && currentClient == client {
		client.Shutdown()
		delete(chatQueue.clients, userID)
	}
	chatQueue.mu.Unlock()
	if ok && currentClient == client && s.ZeroLogger != nil {
		s.Info(utils.USER_LEFT_QUEUE_MESSAGE)
	}
}

// 检查用户是否在队列中
func (s *ChatHub) IsUserInQueue(userID string) bool {
	chatQueue.mu.RLock()
	_, exists := chatQueue.clients[userID]
	chatQueue.mu.RUnlock()
	return exists
}

// 获取队列中的用户
func (s *ChatHub) GetUserFromQueue(userID string) (*Client, bool) {
	chatQueue.mu.RLock()
	client, exists := chatQueue.clients[userID]
	chatQueue.mu.RUnlock()
	return client, exists
}

// 向队列中的用户发送消息
func (s *ChatHub) SendMessageToQueue(userID string, message []byte) bool {
	if client, exists := s.GetUserFromQueue(userID); exists {
		// 如果客户端没有WebSocket连接（手动加入队列的用户），直接返回false
		if client.Conn == nil {
			if s.ZeroLogger != nil {
				s.Warning(utils.USER_IN_QUEUE_NOT_CONNECTED_WARNING)
			}
			return false
		}

		if client.SafeSend(message) {
			return true
		}

		// 发送失败，移除用户
		s.LeaveQueueIfMatch(userID, client)
		return false
	}
	return false
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
		chatHub.LeaveQueueIfMatch(c.UserID, c)
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

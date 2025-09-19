package chat

import (
	"encoding/json"
	"gin_proj/entity/dto"
	"log"
	"sync"

	"github.com/gorilla/websocket"
)

// WebSocket客户端
type Client struct {
	UserID string
	Conn   *websocket.Conn
	Send   chan []byte
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

type ChatHub struct{}

// 加入队列
func (s *ChatHub) JoinQueue(userID string, client *Client) {
	chatQueue.mu.Lock()
	chatQueue.clients[userID] = client
	chatQueue.mu.Unlock()
	log.Printf("用户 %s 已加入聊天队列", userID)
}

// 离开队列
func (s *ChatHub) LeaveQueue(userID string) {
	chatQueue.mu.Lock()
	if client, ok := chatQueue.clients[userID]; ok {
		close(client.Send)
		delete(chatQueue.clients, userID)
	}
	chatQueue.mu.Unlock()
	log.Printf("用户 %s 已离开聊天队列", userID)
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
			log.Printf("用户 %s 在队列中但没有WebSocket连接，无法发送实时消息", userID)
			return false
		}

		select {
		case client.Send <- message:
			return true
		default:
			// 发送失败，移除用户
			s.LeaveQueue(userID)
			return false
		}
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

func (c *Client) ReadPump() {
	defer func() {
		chatHub := &ChatHub{}
		chatHub.LeaveQueue(c.UserID)
		c.Conn.Close()
	}()

	c.Conn.SetReadLimit(512)
	for {
		_, messageBytes, err := c.Conn.ReadMessage()
		if err != nil {
			if websocket.IsUnexpectedCloseError(err, websocket.CloseGoingAway, websocket.CloseAbnormalClosure) {
				log.Printf("websocket error: %v", err)
			}
			break
		}

		// 解析消息
		var wsMessage dto.WebSocketMessage
		if err := json.Unmarshal(messageBytes, &wsMessage); err != nil {
			log.Printf("解析消息失败: %v", err)
			continue
		}

		// 处理ping消息
		if wsMessage.Type == "ping" {
			pongMessage := dto.WebSocketMessage{Type: "pong"}
			pongBytes, _ := json.Marshal(pongMessage)
			select {
			case c.Send <- pongBytes:
			default:
				close(c.Send)
				return
			}
		}
	}
}

func (c *Client) WritePump() {
	defer c.Conn.Close()

	for message := range c.Send {
		c.Conn.WriteMessage(websocket.TextMessage, message)
	}
	c.Conn.WriteMessage(websocket.CloseMessage, []byte{})
}

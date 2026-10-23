package hub

import (
	"context"
	"encoding/json"
	"fmt"
	"strconv"
	"sync"
	"sync/atomic"
	"time"

	"app/common/constants"
	"app/common/utils"
	"app/internal/types"

	"github.com/gorilla/websocket"
)

// WebSocket客户端
type Client struct {
	UserID       int64
	ConnectionID string
	hub          *ChatHub
	Conn         *websocket.Conn
	Send         chan []byte
	MarkRead     func(context.Context, int64, int64, uint64) error
	closeOnce    sync.Once
	*utils.ZeroLogger
}

var chatConnectionSeq atomic.Uint64

// 聊天在线连接队列，按用户与连接 ID 两级索引管理 WebSocket 客户端
type ChatQueue struct {
	clients map[int64]map[string]*Client // userID -> connectionID -> client
	mu      sync.RWMutex
}

// 聊天中心管理，聚合连接队列与消息已读回执写入能力
type ChatHub struct {
	queue    *ChatQueue
	markRead func(context.Context, int64, int64, uint64) error
	*utils.ZeroLogger
}

// NewChatQueue 创建空的聊天连接队列
func NewChatQueue() *ChatQueue {
	return &ChatQueue{clients: make(map[int64]map[string]*Client)}
}

// NewChatHub 创建聊天 Hub 并初始化空队列
func NewChatHub(logger *utils.ZeroLogger) *ChatHub {
	return &ChatHub{queue: NewChatQueue(), ZeroLogger: logger}
}

// ConfigureReadMarker 在服务装配阶段注入消息已读操作
func (s *ChatHub) ConfigureReadMarker(markRead func(context.Context, int64, int64, uint64) error) {
	s.markRead = markRead
}

// HandleWebSocketConnection 接管已升级的连接并启动读写处理，ctx 取请求上下文：连接级 logger 由它派生，加入/离开队列等日志才能带上建立连接时的 trace_id
func (s *ChatHub) HandleWebSocketConnection(ctx context.Context, conn *websocket.Conn, userID int64) {
	client := &Client{
		UserID:       userID,
		ConnectionID: NewConnectionID("ws"),
		Conn:         conn,
		Send:         make(chan []byte, constants.WebSocketSendBufferSize),
		MarkRead:     s.markRead,
	}
	if s.ZeroLogger != nil && ctx != nil {
		client.ZeroLogger = s.ZeroLogger.WithContext(ctx)
	}
	s.JoinQueue(userID, client)
	utils.SafeGo(s.ZeroLogger, "websocket_write_pump", client.WritePump)
	utils.SafeGo(s.ZeroLogger, "websocket_read_pump", client.ReadPump)
}

// NewConnectionID 生成连接标识
func NewConnectionID(prefix string) string {
	return prefix + "-" + strconv.FormatInt(time.Now().UnixNano(), 10) + "-" + strconv.FormatUint(chatConnectionSeq.Add(1), 10)
}

// 加入队列
func (s *ChatHub) JoinQueue(userID int64, client *Client) {
	if client == nil {
		return
	}
	if client.ConnectionID == "" {
		client.ConnectionID = NewConnectionID("ws")
	}

	queue := s.queue
	if queue == nil {
		queue = NewChatQueue()
		s.queue = queue
	}
	queue.mu.Lock()
	if _, ok := queue.clients[userID]; !ok {
		queue.clients[userID] = make(map[string]*Client)
	}
	queue.clients[userID][client.ConnectionID] = client
	client.hub = s
	queue.mu.Unlock()
	// 已有连接级 logger（带请求链路）时保留，不要被根 logger 覆盖
	if client.ZeroLogger == nil && s.ZeroLogger != nil {
		client.ZeroLogger = s.ZeroLogger
	}
	if client.ZeroLogger != nil {
		client.ZeroLogger.Info(constants.USER_JOINED_QUEUE_MESSAGE)
	}
}

// 离开队列
func (s *ChatHub) LeaveQueue(userID int64) {
	queue := s.queue
	if queue == nil {
		return
	}
	// 优先沿用连接级 logger（带建立连接时的链路），没有时回落到根 logger
	var logger *utils.ZeroLogger
	queue.mu.Lock()
	if clients, ok := queue.clients[userID]; ok {
		delete(queue.clients, userID)
		for _, client := range clients {
			if logger == nil {
				logger = client.ZeroLogger
			}
			client.Shutdown()
		}
	}
	queue.mu.Unlock()
	if logger == nil {
		logger = s.ZeroLogger
	}
	if logger != nil {
		logger.Info(constants.USER_LEFT_QUEUE_MESSAGE)
	}
}

// LeaveQueueIfMatch 仅当当前队列中的 client 与传入实例一致时才移除，避免旧连接退出时误删新连接
func (s *ChatHub) LeaveQueueIfMatch(ctx context.Context, userID int64, connectionID string, client *Client) {
	if client == nil || connectionID == "" {
		return
	}

	queue := s.queue
	if queue == nil {
		return
	}
	queue.mu.Lock()
	currentClients, ok := queue.clients[userID]
	currentClient, exists := currentClients[connectionID]
	if ok && exists && currentClient == client {
		client.Shutdown()
		delete(currentClients, connectionID)
		if len(currentClients) == 0 {
			delete(queue.clients, userID)
		}
	}
	queue.mu.Unlock()
	if ok && exists && currentClient == client {
		logger := client.ZeroLogger
		if logger == nil {
			logger = s.ZeroLogger
		}
		if logger != nil {
			logger.Info(constants.USER_LEFT_QUEUE_MESSAGE)
		}
	}
}

// 检查用户是否在队列中
func (s *ChatHub) IsUserInQueue(userID int64) bool {
	queue := s.queue
	if queue == nil {
		return false
	}
	queue.mu.RLock()
	clients, exists := queue.clients[userID]
	userExists := exists && len(clients) > 0
	queue.mu.RUnlock()
	return userExists
}

// 获取队列中的用户
func (s *ChatHub) GetUserFromQueue(userID int64) (*Client, bool) {
	queue := s.queue
	if queue == nil {
		return nil, false
	}
	queue.mu.RLock()
	clients, exists := queue.clients[userID]
	var client *Client
	if exists {
		for _, item := range clients {
			client = item
			break
		}
	}
	queue.mu.RUnlock()
	return client, client != nil
}

// GetUserClients 获取指定用户的全部连接副本
func (s *ChatHub) GetUserClients(userID int64) []*Client {
	queue := s.queue
	if queue == nil {
		return nil
	}
	queue.mu.RLock()
	defer queue.mu.RUnlock()

	clients, exists := queue.clients[userID]
	if !exists || len(clients) == 0 {
		return nil
	}

	result := make([]*Client, 0, len(clients))
	for _, client := range clients {
		result = append(result, client)
	}
	return result
}

// 向队列中的用户发送消息，ctx 由触发本次投递的链路提供，日志据此关联 trace_id
func (s *ChatHub) SendMessageToQueue(ctx context.Context, userID int64, message []byte) bool {
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
		s.LeaveQueueIfMatch(ctx, userID, client.ConnectionID, client)
	}

	// 优先沿用连接级 logger（带建立连接时的链路），没有时回落到根 logger
	logger := s.ZeroLogger
	if logger != nil {
		if len(clients) > 0 && clients[0] != nil && clients[0].ZeroLogger != nil {
			logger = clients[0].ZeroLogger
		} else {
			logger = logger.WithContext(ctx)
		}
	}
	if !sentAny && logger != nil {
		logger.Warning(constants.USER_IN_QUEUE_NOT_CONNECTED_WARNING)
	}

	return sentAny
}

// 获取队列中所有用户
func (s *ChatHub) GetAllUsersInQueue() []int64 {
	queue := s.queue
	if queue == nil {
		return nil
	}
	queue.mu.RLock()
	defer queue.mu.RUnlock()

	users := make([]int64, 0, len(queue.clients))
	for userID := range queue.clients {
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

// ReadPump 持续读取 WebSocket 消息，处理心跳应答与已读回执，连接断开时从队列移除自身
func (c *Client) ReadPump() {
	defer func() {
		chatHub := c.hub
		if chatHub == nil {
			chatHub = NewChatHub(c.ZeroLogger)
		}
		// 离开队列的日志优先使用连接级 logger（已带建立连接时的 trace_id），此处 ctx 仅占位
		chatHub.LeaveQueueIfMatch(context.Background(), c.UserID, c.ConnectionID, c)
	}()

	c.Conn.SetReadLimit(constants.WebSocketReadLimit)
	_ = c.Conn.SetReadDeadline(time.Now().Add(constants.WebSocketPongWait))
	c.Conn.SetPongHandler(func(string) error {
		return c.Conn.SetReadDeadline(time.Now().Add(constants.WebSocketPongWait))
	})
	for {
		_, messageBytes, err := c.Conn.ReadMessage()
		if err != nil {
			if websocket.IsUnexpectedCloseError(err, websocket.CloseGoingAway, websocket.CloseAbnormalClosure) {
				if c.ZeroLogger != nil {
					c.Error(fmt.Sprintf(constants.WS_ERROR, err))
				}
			}
			break
		}

		// 解析消息
		var wsMessage types.ChatWsMessage
		if err := json.Unmarshal(messageBytes, &wsMessage); err != nil {
			if c.ZeroLogger != nil {
				c.Error(fmt.Sprintf(constants.PARSE_MESSAGE_FAIL, err))
			}
			continue
		}

		switch wsMessage.Type {
		case constants.HEARTBEAT_MESSAGE:
			pongMessage := types.ChatWsMessage{Type: constants.HEARTBEAT_RESPONSE}
			pongBytes, err := json.Marshal(pongMessage)
			if err != nil {
				if c.ZeroLogger != nil {
					c.Error(fmt.Sprintf(constants.WS_HEARTBEAT_RESPONSE_FAIL, err))
				}
				return
			}
			if !c.SafeSend(pongBytes) {
				return
			}
		case constants.READ_RECEIPT_MESSAGE:
			if err := c.handleReadReceipt(&wsMessage); err != nil && c.ZeroLogger != nil {
				c.Error(fmt.Sprintf(constants.WS_READ_RECEIPT_HANDLE_FAIL, err))
			}
		}
	}
}

// handleReadReceipt 处理已读回执消息，调用 MarkRead 标记已读并向客户端回执确认
func (c *Client) handleReadReceipt(message *types.ChatWsMessage) error {
	if message == nil || message.SenderId <= 0 || message.MessageId == 0 {
		return fmt.Errorf("%s", constants.WS_READ_RECEIPT_INVALID)
	}
	if c.MarkRead == nil {
		return fmt.Errorf("%s", constants.WS_READ_RECEIPT_INVALID)
	}

	ctx, cancel := context.WithTimeout(context.Background(), constants.WebSocketReadReceiptTimeout)
	defer cancel()
	if err := c.MarkRead(ctx, c.UserID, message.SenderId, message.MessageId); err != nil {
		return err
	}

	ackBytes, err := json.Marshal(types.ChatWsMessage{
		Type:       constants.READ_RECEIPT_ACK,
		SenderId:   message.SenderId,
		ReceiverId: c.UserID,
		MessageId:  message.MessageId,
	})
	if err != nil {
		return err
	}
	if !c.SafeSend(ackBytes) {
		return fmt.Errorf("%s", constants.WS_READ_RECEIPT_ACK_FAIL)
	}
	return nil
}

// WritePump 将发送队列中的消息写出并按周期发送 Ping 保活，写出失败或队列关闭时退出
func (c *Client) WritePump() {
	defer c.Shutdown()
	pingTicker := time.NewTicker(constants.WebSocketPingInterval)
	defer pingTicker.Stop()

	for {
		select {
		case message, ok := <-c.Send:
			if !ok {
				return
			}
			_ = c.Conn.SetWriteDeadline(time.Now().Add(constants.WebSocketWriteWait))
			if err := c.Conn.WriteMessage(websocket.TextMessage, message); err != nil {
				if c.ZeroLogger != nil {
					c.Error(fmt.Sprintf(constants.WS_WRITE_MESSAGE_FAIL, err))
				}
				return
			}
		case <-pingTicker.C:
			if err := c.Conn.WriteControl(websocket.PingMessage, nil, time.Now().Add(constants.WebSocketWriteWait)); err != nil {
				if c.ZeroLogger != nil {
					c.Error(fmt.Sprintf(constants.WS_WRITE_MESSAGE_FAIL, err))
				}
				return
			}
		}
	}
}

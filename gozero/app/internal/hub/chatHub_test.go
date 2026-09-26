package hub

import (
	"context"
	"encoding/json"
	"errors"
	"testing"

	"app/common/constants"
	"app/internal/types"

	"github.com/gorilla/websocket"
)

// 验证该测试场景的预期行为

func TestHandleReadReceiptUsesConnectedUserAndAcknowledges(t *testing.T) {
	var receiverID int64
	var senderID int64
	var lastMessageID uint64
	client := &Client{
		UserID: 7,
		Send:   make(chan []byte, 1),
		MarkRead: func(_ context.Context, receiver, sender int64, messageID uint64) error {
			receiverID = receiver
			senderID = sender
			lastMessageID = messageID
			return nil
		},
	}

	err := client.handleReadReceipt(&types.ChatWsMessage{
		Type:      constants.READ_RECEIPT_MESSAGE,
		SenderId:  42,
		MessageId: 123,
	})
	if err != nil {
		t.Fatalf("处理已读回执失败: %v", err)
	}
	if receiverID != 7 || senderID != 42 || lastMessageID != 123 {
		t.Fatalf("已读范围错误: receiver=%d sender=%d message=%d", receiverID, senderID, lastMessageID)
	}

	var ack types.ChatWsMessage
	if err := json.Unmarshal(<-client.Send, &ack); err != nil {
		t.Fatalf("解析已读确认失败: %v", err)
	}
	if ack.Type != constants.READ_RECEIPT_ACK || ack.ReceiverId != 7 || ack.SenderId != 42 || ack.MessageId != 123 {
		t.Fatalf("已读确认内容错误: %+v", ack)
	}
}

// 验证该测试场景的预期行为

func TestHandleReadReceiptRejectsMissingMessageID(t *testing.T) {
	called := false
	client := &Client{
		UserID: 7,
		Send:   make(chan []byte, 1),
		MarkRead: func(context.Context, int64, int64, uint64) error {
			called = true
			return nil
		},
	}

	err := client.handleReadReceipt(&types.ChatWsMessage{
		Type:     constants.READ_RECEIPT_MESSAGE,
		SenderId: 42,
	})
	if err == nil {
		t.Fatal("缺少 message_id 的已读回执应被拒绝")
	}
	if called {
		t.Fatal("无效已读回执不应访问数据库")
	}
}

// 验证该测试场景的预期行为

func TestHandleReadReceiptDoesNotAcknowledgeFailedPersistence(t *testing.T) {
	client := &Client{
		UserID: 7,
		Send:   make(chan []byte, 1),
		MarkRead: func(context.Context, int64, int64, uint64) error {
			return errors.New("database failed")
		},
	}

	err := client.handleReadReceipt(&types.ChatWsMessage{
		Type:      constants.READ_RECEIPT_MESSAGE,
		SenderId:  42,
		MessageId: 123,
	})
	if err == nil || err.Error() != "database failed" {
		t.Fatalf("期望保留持久化错误，实际为 %v", err)
	}
	if len(client.Send) != 0 {
		t.Fatal("持久化失败后不应发送已读确认")
	}
}

// 验证该测试场景的预期行为

func TestChatHubKeepsOtherConnectionsWhenOneConnectionLeaves(t *testing.T) {
	resetChatQueueForTest(t)
	hub := &ChatHub{}
	first := &Client{ConnectionID: "first", Send: make(chan []byte, 1)}
	second := &Client{ConnectionID: "second", Send: make(chan []byte, 1)}
	hub.JoinQueue(7, first)
	hub.JoinQueue(7, second)

	hub.LeaveQueueIfMatch(7, first.ConnectionID, first)

	clients := hub.GetUserClients(7)
	if len(clients) != 1 || clients[0] != second {
		t.Fatalf("移除单个连接后剩余连接错误: %+v", clients)
	}
	if !hub.IsUserInQueue(7) {
		t.Fatal("用户仍有连接时应保持在线")
	}
}

// 验证该测试场景的预期行为

func TestChatHubOldConnectionCannotRemoveReplacement(t *testing.T) {
	resetChatQueueForTest(t)
	hub := &ChatHub{}
	oldClient := &Client{ConnectionID: "same", Send: make(chan []byte, 1)}
	newClient := &Client{ConnectionID: "same", Send: make(chan []byte, 1)}
	hub.JoinQueue(7, oldClient)
	hub.JoinQueue(7, newClient)

	hub.LeaveQueueIfMatch(7, oldClient.ConnectionID, oldClient)

	client, ok := hub.GetUserFromQueue(7)
	if !ok || client != newClient {
		t.Fatal("旧连接退出不应移除同标识的新连接")
	}
}

// 验证该测试场景的预期行为

func TestRealtimeDispatcherPrefersWebSocketDelivery(t *testing.T) {
	resetChatQueueForTest(t)
	chatHub := &ChatHub{}
	wsClient := &Client{
		ConnectionID: "ws-1",
		Conn:         &websocket.Conn{},
		Send:         make(chan []byte, 1),
	}
	chatHub.JoinQueue(7, wsClient)
	sseHub := newSSEHubForTest()
	sseMessages := make(chan any, 1)
	sseHub.RegisterClient(7, "sse-1", sseMessages, make(chan bool))
	dispatcher := NewChatRealtimeDispatcher(chatHub, sseHub, nil)
	event := ChatRealtimeEvent{
		ReceiverID:       7,
		WebSocketMessage: &types.ChatWsMessage{Type: "message", MessageId: 12},
		SSENotification: &types.ChatSSEMessage{
			Type:    "message",
			Message: &types.ChatMessageItem{Id: 12},
		},
	}
	payload, _ := json.Marshal(event)

	dispatcher.Handle(payload)

	if len(wsClient.Send) != 1 {
		t.Fatal("在线 WebSocket 应收到实时消息")
	}
	if len(sseMessages) != 0 {
		t.Fatal("WebSocket 投递成功后不应重复发送 SSE 通知")
	}
}

// 验证该测试场景的预期行为

func TestRealtimeDispatcherFallsBackToSSEWithoutWebSocket(t *testing.T) {
	resetChatQueueForTest(t)
	sseHub := newSSEHubForTest()
	sseMessages := make(chan any, 1)
	sseHub.RegisterClient(7, "sse-1", sseMessages, make(chan bool))
	dispatcher := NewChatRealtimeDispatcher(&ChatHub{}, sseHub, nil)
	event := ChatRealtimeEvent{
		ReceiverID:       7,
		WebSocketMessage: &types.ChatWsMessage{Type: "message", MessageId: 12},
		SSENotification: &types.ChatSSEMessage{
			Type:    "message",
			Message: &types.ChatMessageItem{Id: 12},
		},
	}
	payload, _ := json.Marshal(event)

	dispatcher.Handle(payload)

	select {
	case notification := <-sseMessages:
		message, ok := notification.(*types.ChatSSEMessage)
		if !ok || message.Message == nil || message.Message.Id != 12 {
			t.Fatalf("SSE 回退消息错误: %+v", notification)
		}
	default:
		t.Fatal("WebSocket 不在线时应回退发送 SSE 通知")
	}
}

// 验证该测试场景的预期行为

func TestSSEHubTargetsAllConnectionsForUserOnly(t *testing.T) {
	hub := newSSEHubForTest()
	first := make(chan any, 1)
	second := make(chan any, 1)
	other := make(chan any, 1)
	hub.RegisterClient(7, "first", first, make(chan bool))
	hub.RegisterClient(7, "second", second, make(chan bool))
	hub.RegisterClient(8, "other", other, make(chan bool))
	notification := &types.ChatSSEMessage{
		Type:    "message",
		Message: &types.ChatMessageItem{Id: 99},
	}

	hub.SendNotificationToUser(7, notification)

	if len(first) != 1 || len(second) != 1 {
		t.Fatal("目标用户的所有 SSE 连接都应收到通知")
	}
	if len(other) != 0 {
		t.Fatal("其他用户不应收到通知")
	}
}

func resetChatQueueForTest(t *testing.T) {
	t.Helper()
	chatQueue.mu.Lock()
	chatQueue.clients = make(map[int64]map[string]*Client)
	chatQueue.mu.Unlock()
	t.Cleanup(func() {
		chatQueue.mu.Lock()
		chatQueue.clients = make(map[int64]map[string]*Client)
		chatQueue.mu.Unlock()
	})
}

func newSSEHubForTest() *SSEHubManager {
	return &SSEHubManager{clients: make(map[int64]map[string]*SSEClient)}
}

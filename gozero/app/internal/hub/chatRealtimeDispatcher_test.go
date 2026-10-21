package hub

import (
	"encoding/json"
	"testing"

	"app/internal/types"

	"github.com/gorilla/websocket"
)

// 构造实时事件的合法 JSON 载荷，编组失败直接终止测试

func marshalRealtimeEventForTest(t *testing.T, event ChatRealtimeEvent) []byte {
	t.Helper()
	payload, err := json.Marshal(event)
	if err != nil {
		t.Fatalf("编组实时事件失败: %v", err)
	}
	return payload
}

// 在线 WebSocket 连接命中队列时应优先走 WS 投递，且不再重复发送 SSE 通知

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
	payload := marshalRealtimeEventForTest(t, event)

	dispatcher.Handle(payload)

	if len(wsClient.Send) != 1 {
		t.Fatal("在线 WebSocket 应收到实时消息")
	}
	if len(sseMessages) != 0 {
		t.Fatal("WebSocket 投递成功后不应重复发送 SSE 通知")
	}
}

// WebSocket 不在线时应回退发送 SSE 通知

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
	payload := marshalRealtimeEventForTest(t, event)

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

// 非法事件不得触发任何投递，也不得 panic

func TestRealtimeDispatcherIgnoresInvalidEvents(t *testing.T) {
	wsMessage := &types.ChatWsMessage{Type: "message", MessageId: 12}
	sseNotification := &types.ChatSSEMessage{
		Type:    "message",
		Message: &types.ChatMessageItem{Id: 12},
	}
	cases := []struct {
		name    string
		payload []byte
	}{
		{
			name:    "非法JSON",
			payload: []byte("{invalid"),
		},
		{
			name:    "接收者ID非正数",
			payload: marshalRealtimeEventForTest(t, ChatRealtimeEvent{ReceiverID: 0, WebSocketMessage: wsMessage, SSENotification: sseNotification}),
		},
		{
			name:    "缺少WebSocket消息",
			payload: marshalRealtimeEventForTest(t, ChatRealtimeEvent{ReceiverID: 7, SSENotification: sseNotification}),
		},
		{
			name:    "缺少SSE通知",
			payload: marshalRealtimeEventForTest(t, ChatRealtimeEvent{ReceiverID: 7, WebSocketMessage: wsMessage}),
		},
	}

	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
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

			dispatcher.Handle(tc.payload)

			if len(wsClient.Send) != 0 {
				t.Fatal("非法事件不应投递到 WebSocket")
			}
			if len(sseMessages) != 0 {
				t.Fatal("非法事件不应投递到 SSE")
			}
		})
	}
}

// nil 分发器处理事件不应 panic

func TestRealtimeDispatcherNilReceiverDoesNotPanic(t *testing.T) {
	var dispatcher *ChatRealtimeDispatcher
	dispatcher.Handle([]byte("{}"))
}

package hub

import "app/internal/types"

// ChatRealtimeEvent 跨 Pod 传递的聊天实时事件
// 仅服务内部使用，不对外暴露；对外帧结构见 ChatSSEMessage 与 ChatWsMessage
type ChatRealtimeEvent struct {
	Type             string                `json:"type"`
	ReceiverID       int64                 `json:"receiver_id"`
	WebSocketMessage *types.ChatWsMessage  `json:"websocket_message,omitempty"`
	SSENotification  *types.ChatSSEMessage `json:"sse_notification,omitempty"`
}

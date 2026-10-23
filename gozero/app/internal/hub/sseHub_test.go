package hub

import (
	"context"
	"testing"

	"app/internal/types"
)

// 验证该测试场景的预期行为

func TestSSEHubRegisterSendAndUnregister(t *testing.T) {
	hub := newSSEHubForTest()
	send := make(chan any, 1)
	hub.RegisterClient(context.Background(), 7, "connection", send, make(chan bool))
	hub.SendNotificationToUser(context.Background(), 7, &types.ChatSSEMessage{Type: "message"})
	if len(send) != 1 {
		t.Fatal("registered client should receive notification")
	}
	hub.UnregisterClient(context.Background(), 7, "connection")
	if len(hub.clients) != 0 {
		t.Fatal("last client should be removed from hub")
	}
}

// 验证该测试场景的预期行为

func TestSSEHubIgnoresEmptyConnectionIDAndNilNotification(t *testing.T) {
	hub := newSSEHubForTest()
	send := make(chan any, 1)
	hub.RegisterClient(context.Background(), 7, "", send, make(chan bool))
	hub.SendNotificationToUser(context.Background(), 7, nil)
	if len(hub.clients) != 0 || len(send) != 0 {
		t.Fatal("invalid registration or notification should be ignored")
	}
}

// 验证该测试场景的预期行为

func TestFormatSSEMessage(t *testing.T) {
	if FormatSSEMessage(nil) != "" {
		t.Fatal("nil SSE payload should be empty")
	}
	message := FormatSSEMessage(map[string]string{"type": "message"})
	if message != "data: {\"type\":\"message\"}\n\n" {
		t.Fatalf("unexpected SSE format: %q", message)
	}
}

// 验证该测试场景的预期行为

func TestSSEHubBroadcastsToAllUsers(t *testing.T) {
	hub := newSSEHubForTest()
	first := make(chan any, 1)
	second := make(chan any, 1)
	hub.RegisterClient(context.Background(), 7, "first", first, make(chan bool))
	hub.RegisterClient(context.Background(), 8, "second", second, make(chan bool))
	hub.BroadcastNotification(context.Background(), "broadcast")
	if <-first != "broadcast" || <-second != "broadcast" {
		t.Fatal("broadcast should reach every registered client")
	}
}

package chat

import (
	"context"
	"errors"
	"testing"

	"app/internal/types"
)

// 验证发送消息时保存裁剪后的内容并实时通知接收者
func TestChatSendMessagePersistsTrimmedContentAndNotifiesReceiver(t *testing.T) {
	for _, brokenBus := range []bool{false, true} {
		t.Run(map[bool]string{false: "本地分发", true: "发布失败后本地回退"}[brokenBus], func(t *testing.T) {
			model := &chatMessageModelFake{unread: map[int64]int64{1: 3}}
			ctx, notifications := newChatMessageTestContext(t, model, brokenBus)
			logic := NewChatSendMessageLogic(context.Background(), ctx)
			t.Cleanup(func() { _ = logic.ZeroLogger.Close() })

			response, err := logic.ChatSendMessage(&types.ChatSendMessageReq{SenderId: 1, ReceiverId: 2, Content: "  你好  "})
			if err != nil || response == nil || response.MessageId != 42 {
				t.Fatalf("发送结果不正确: %+v, %v", response, err)
			}
			if model.created == nil || model.created.Content != "你好" || model.created.SenderId != 1 || model.created.ReceiverId != 2 {
				t.Fatalf("保存的消息不正确: %+v", model.created)
			}
			select {
			case value := <-notifications:
				notification, ok := value.(*types.ChatSSEMessage)
				if !ok || notification.Message == nil || notification.Message.Id != 42 || notification.UnreadCounts[1] != 3 {
					t.Fatalf("实时通知内容不正确: %+v", value)
				}
			default:
				t.Fatal("接收者没有收到实时通知")
			}
		})
	}
}

// 验证落库失败时不发送实时通知
func TestChatSendMessageDoesNotNotifyWhenPersistenceFails(t *testing.T) {
	model := &chatMessageModelFake{createErr: errors.New("write failed")}
	ctx, notifications := newChatMessageTestContext(t, model, false)
	logic := NewChatSendMessageLogic(context.Background(), ctx)
	t.Cleanup(func() { _ = logic.ZeroLogger.Close() })

	response, err := logic.ChatSendMessage(&types.ChatSendMessageReq{SenderId: 1, ReceiverId: 2, Content: "你好"})
	if err == nil || response != nil {
		t.Fatalf("落库失败应返回错误: %+v, %v", response, err)
	}
	select {
	case value := <-notifications:
		t.Fatalf("落库失败不应发送通知: %+v", value)
	default:
	}
}

// 验证未读数查询失败时降级为空未读数且不阻断已保存的消息
func TestChatSendMessageUsesEmptyUnreadCountsWhenQueryFails(t *testing.T) {
	model := &chatMessageModelFake{unreadErr: errors.New("read failed")}
	ctx, notifications := newChatMessageTestContext(t, model, false)
	logic := NewChatSendMessageLogic(context.Background(), ctx)
	t.Cleanup(func() { _ = logic.ZeroLogger.Close() })

	response, err := logic.ChatSendMessage(&types.ChatSendMessageReq{SenderId: 1, ReceiverId: 2, Content: "你好"})
	if err != nil || response == nil {
		t.Fatalf("未读数查询失败不应阻断已保存的消息: %+v, %v", response, err)
	}
	notification := (<-notifications).(*types.ChatSSEMessage)
	if len(notification.UnreadCounts) != 0 {
		t.Fatalf("查询失败时未读数应为空: %+v", notification.UnreadCounts)
	}
}

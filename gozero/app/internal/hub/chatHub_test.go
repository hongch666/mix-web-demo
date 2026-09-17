package hub

import (
	"context"
	"encoding/json"
	"testing"

	"app/common/constants"
	"app/internal/types"
)

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

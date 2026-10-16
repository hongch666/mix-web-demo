package chat

import (
	"context"
	"errors"
	"testing"
	"time"

	"app/common/pubsub"
	"app/common/utils"
	"app/internal/hub"
	"app/internal/svc"
	"app/internal/types"
	"app/model/chatMessages"
)

type chatMessageModelFake struct {
	chatMessages.ChatMessagesModel
	created       *chatMessages.ChatMessages
	createErr     error
	unread        map[int64]int64
	unreadErr     error
	messages      []*chatMessages.ChatMessages
	total         int64
	historyErr    error
	markErr       error
	historyOffset int
	historyLimit  int
	markCalled    bool
}

func (m *chatMessageModelFake) CreateChatMessage(_ context.Context, message *chatMessages.ChatMessages) error {
	m.created = message
	if m.createErr == nil {
		message.Id = 42
		message.CreatedAt = time.Date(2026, 1, 2, 3, 4, 5, 0, time.UTC)
	}
	return m.createErr
}

func (m *chatMessageModelFake) GetAllUnreadCounts(_ context.Context, _ int64) (map[int64]int64, error) {
	return m.unread, m.unreadErr
}

func (m *chatMessageModelFake) GetChatHistory(_ context.Context, _, _ int64, offset, limit int) ([]*chatMessages.ChatMessages, int64, error) {
	m.historyOffset, m.historyLimit = offset, limit
	return m.messages, m.total, m.historyErr
}

func (m *chatMessageModelFake) MarkChatHistoryAsRead(_ context.Context, _, _ int64) error {
	m.markCalled = true
	return m.markErr
}

func newChatMessageTestContext(t *testing.T, model *chatMessageModelFake, withBrokenBus bool) (*svc.ServiceContext, chan any) {
	t.Helper()
	logger, err := utils.NewZeroLogger(t.TempDir())
	if err != nil {
		t.Fatalf("创建测试日志器失败: %v", err)
	}
	t.Cleanup(func() { _ = logger.Close() })
	sseHub := hub.NewSSEHub(logger)
	notifications := make(chan any, 1)
	sseHub.RegisterClient(2, "receiver", notifications, make(chan bool))
	chatHub := hub.NewChatHub(logger)
	hubContext := &svc.HubContext{
		ChatHub:            chatHub,
		SSEHub:             sseHub,
		RealtimeDispatcher: hub.NewChatRealtimeDispatcher(chatHub, sseHub, logger),
	}
	if withBrokenBus {
		hubContext.RealtimeBus = pubsub.NewRedisPubSub(nil, logger, "chat-events")
	}
	return &svc.ServiceContext{
		ModelContext:  &svc.ModelContext{ChatMessagesModel: model},
		HubContext:    hubContext,
		LoggerContext: &svc.LoggerContext{Logger: logger},
	}, notifications
}

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

func TestChatGetHistoryNormalizesPageAndMapsMessages(t *testing.T) {
	model := &chatMessageModelFake{
		messages: []*chatMessages.ChatMessages{{Id: 7, SenderId: 1, ReceiverId: 2, Content: "你好", CreatedAt: time.Date(2026, 1, 2, 3, 4, 5, 0, time.UTC)}},
		total:    1,
	}
	ctx, _ := newChatMessageTestContext(t, model, false)
	logic := NewChatGetHistoryLogic(context.Background(), ctx)
	t.Cleanup(func() { _ = logic.ZeroLogger.Close() })

	response, err := logic.ChatGetHistory(&types.ChatGetHistoryReq{UserId: 2, OtherId: 1, Page: 0, Size: 0})
	if err != nil || response == nil || response.Total != 1 || len(response.Messages) != 1 {
		t.Fatalf("历史记录映射不正确: %+v, %v", response, err)
	}
	if model.historyOffset != 0 || model.historyLimit != 20 || !model.markCalled || response.Messages[0].IsRead != 1 || response.Messages[0].Id != 7 {
		t.Fatalf("分页或已读状态不正确: offset=%d limit=%d mark=%v messages=%+v", model.historyOffset, model.historyLimit, model.markCalled, response.Messages)
	}
}

func TestChatGetHistoryReportsQueryFailureAndToleratesMarkFailure(t *testing.T) {
	for _, testCase := range []struct {
		name       string
		historyErr error
		markErr    error
		wantError  bool
	}{
		{name: "查询失败", historyErr: errors.New("read failed"), wantError: true},
		{name: "标记已读失败", markErr: errors.New("mark failed")},
	} {
		t.Run(testCase.name, func(t *testing.T) {
			model := &chatMessageModelFake{historyErr: testCase.historyErr, markErr: testCase.markErr}
			ctx, _ := newChatMessageTestContext(t, model, false)
			logic := NewChatGetHistoryLogic(context.Background(), ctx)
			t.Cleanup(func() { _ = logic.ZeroLogger.Close() })

			response, err := logic.ChatGetHistory(&types.ChatGetHistoryReq{UserId: 2, OtherId: 1, Page: 3, Size: 5})
			if (err != nil) != testCase.wantError || model.historyOffset != 10 || model.historyLimit != 5 || !model.markCalled {
				t.Fatalf("历史查询结果不正确: response=%+v err=%v offset=%d limit=%d mark=%v", response, err, model.historyOffset, model.historyLimit, model.markCalled)
			}
		})
	}
}

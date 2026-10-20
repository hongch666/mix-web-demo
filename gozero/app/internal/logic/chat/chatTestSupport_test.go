package chat

import (
	"context"
	"testing"
	"time"

	"app/common/pubsub"
	"app/common/utils"
	"app/internal/hub"
	"app/internal/svc"
	"app/model/chatMessages"
)

// chatMessageModelFake 聊天消息模型的内存替身，供各 logic 测试复用
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

	singleUnread  int64
	singleErr     error
	singleUserID  int64
	singleOtherID int64
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

func (m *chatMessageModelFake) GetUnreadCount(_ context.Context, userID, otherID int64) (int64, error) {
	m.singleUserID, m.singleOtherID = userID, otherID
	return m.singleUnread, m.singleErr
}

func (m *chatMessageModelFake) GetChatHistory(_ context.Context, _, _ int64, offset, limit int) ([]*chatMessages.ChatMessages, int64, error) {
	m.historyOffset, m.historyLimit = offset, limit
	return m.messages, m.total, m.historyErr
}

func (m *chatMessageModelFake) MarkChatHistoryAsRead(_ context.Context, _, _ int64) error {
	m.markCalled = true
	return m.markErr
}

// newChatTestLogger 创建测试用日志器并在测试结束后释放
// t.Cleanup 按后进先出执行：先关日志再清理临时目录，
// 否则 Windows 下日志文件句柄未释放会导致清理失败
func newChatTestLogger(t *testing.T) *utils.ZeroLogger {
	t.Helper()
	logger, err := utils.NewZeroLogger(t.TempDir())
	if err != nil {
		t.Fatalf("创建测试日志器失败: %v", err)
	}
	t.Cleanup(func() { _ = logger.Close() })
	return logger
}

func newChatMessageTestContext(t *testing.T, model *chatMessageModelFake, withBrokenBus bool) (*svc.ServiceContext, chan any) {
	t.Helper()
	logger := newChatTestLogger(t)
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

// resolveUserIDCase ResolveUserID 的表驱动用例
type resolveUserIDCase struct {
	name         string
	reqUserID    *int64
	headerUserID string
	want         int64
	wantErr      bool
}

var resolveUserIDTestCases = []resolveUserIDCase{
	{
		name:         "查询参数已由中间件校验并优先使用",
		reqUserID:    ptrInt64(100),
		headerUserID: "999",
		want:         100,
	},
	{
		name:         "查询参数缺省时回退请求头",
		headerUserID: "200",
		want:         200,
	},
	{
		name:         "请求头前后空白被裁剪",
		headerUserID: "  300  ",
		want:         300,
	},
	{
		name:    "查询参数与请求头都缺省时报错",
		wantErr: true,
	},
	{
		name:         "请求头不是数字时报错",
		headerUserID: "abc",
		wantErr:      true,
	},
	{
		name:         "请求头为零时报错",
		headerUserID: "0",
		wantErr:      true,
	},
	{
		name:         "请求头为负数时报错",
		headerUserID: "-5",
		wantErr:      true,
	},
}

func ptrInt64(value int64) *int64 {
	return &value
}

// runResolveUserIDCases 执行 ResolveUserID 共享用例，resolve 由各 logic 测试注入请求类型
func runResolveUserIDCases(t *testing.T, resolve func(reqUserID *int64, headerUserID string) (int64, error)) {
	t.Helper()
	for _, testCase := range resolveUserIDTestCases {
		t.Run(testCase.name, func(t *testing.T) {
			got, err := resolve(testCase.reqUserID, testCase.headerUserID)
			checkResolveResult(t, got, err, testCase.want, testCase.wantErr)
		})
	}
}

func checkResolveResult(t *testing.T, got int64, err error, want int64, wantErr bool) {
	t.Helper()

	if wantErr {
		if err == nil {
			t.Fatalf("期望解析失败, 实际得到 userID=%d", got)
		}
		return
	}

	if err != nil {
		t.Fatalf("期望解析成功, 实际错误: %v", err)
	}

	if got != want {
		t.Errorf("userID = %d, 期望 %d", got, want)
	}
}

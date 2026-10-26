package chat

import (
	"context"
	"errors"
	"testing"
	"time"

	"app/internal/testkit"
	"app/internal/types"
	"app/model/chatMessages"
)

// 验证获取历史记录时归一化分页参数、映射消息并标记已读
func TestChatGetHistoryNormalizesPageAndMapsMessages(t *testing.T) {
	model := &testkit.ChatMessageModelFake{
		Messages: []*chatMessages.ChatMessages{{Id: 7, SenderId: 1, ReceiverId: 2, Content: "你好", CreatedAt: time.Date(2026, 1, 2, 3, 4, 5, 0, time.UTC)}},
		Total:    1,
	}
	ctx, _ := testkit.NewChatMessageTestContext(t, model, false)
	logic := NewChatGetHistoryLogic(context.Background(), ctx)
	t.Cleanup(func() { _ = logic.ZeroLogger.Close() })

	response, err := logic.ChatGetHistory(&types.ChatGetHistoryReq{UserId: 2, OtherId: 1, Page: 0, Size: 0})
	if err != nil || response == nil || response.Total != 1 || len(response.Messages) != 1 {
		t.Fatalf("历史记录映射不正确: %+v, %v", response, err)
	}
	if model.HistoryOffset != 0 || model.HistoryLimit != 20 || !model.MarkCalled || response.Messages[0].IsRead != 1 || response.Messages[0].Id != 7 {
		t.Fatalf("分页或已读状态不正确: offset=%d limit=%d mark=%v messages=%+v", model.HistoryOffset, model.HistoryLimit, model.MarkCalled, response.Messages)
	}
}

// 验证历史记录查询失败返回错误且标记已读失败不阻断
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
			model := &testkit.ChatMessageModelFake{HistoryErr: testCase.historyErr, MarkErr: testCase.markErr}
			ctx, _ := testkit.NewChatMessageTestContext(t, model, false)
			logic := NewChatGetHistoryLogic(context.Background(), ctx)
			t.Cleanup(func() { _ = logic.ZeroLogger.Close() })

			response, err := logic.ChatGetHistory(&types.ChatGetHistoryReq{UserId: 2, OtherId: 1, Page: 3, Size: 5})
			if (err != nil) != testCase.wantError || model.HistoryOffset != 10 || model.HistoryLimit != 5 || !model.MarkCalled {
				t.Fatalf("历史查询结果不正确: response=%+v err=%v offset=%d limit=%d mark=%v", response, err, model.HistoryOffset, model.HistoryLimit, model.MarkCalled)
			}
		})
	}
}

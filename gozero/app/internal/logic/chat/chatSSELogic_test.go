package chat

import (
	"testing"

	"app/internal/types"
)

// 验证 SSE 连接用户解析的查询参数优先、请求头回退与非法输入拒绝
func TestChatSSEResolveUserID(t *testing.T) {
	logger := newChatTestLogger(t)
	sseLogic := &ChatSSELogic{ZeroLogger: logger}

	runResolveUserIDCases(t, func(reqUserID *int64, headerUserID string) (int64, error) {
		return sseLogic.ResolveUserID(&types.ChatSSEConnectReq{UserId: reqUserID}, headerUserID)
	})
}

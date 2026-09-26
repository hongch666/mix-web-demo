package search

import (
	"context"
	"testing"

	"app/common/utils"
	"app/internal/svc"
	"app/internal/types"
)

// 验证搜索历史请求中的用户编号格式错误会被拒绝
func TestGetSearchHistoryRejectsInvalidUserID(t *testing.T) {
	logger, err := utils.NewZeroLogger(t.TempDir())
	if err != nil {
		t.Fatalf("创建测试日志器失败: %v", err)
	}
	t.Cleanup(func() { _ = logger.Close() })
	logic := NewGetSearchHistoryLogic(context.Background(), &svc.ServiceContext{LoggerContext: &svc.LoggerContext{Logger: logger}})
	t.Cleanup(func() { _ = logic.ZeroLogger.Close() })
	if _, err := logic.GetSearchHistory(&types.GetSearchHistoryReq{UserId: "invalid"}); err == nil {
		t.Fatal("非法用户编号应返回错误")
	}
}

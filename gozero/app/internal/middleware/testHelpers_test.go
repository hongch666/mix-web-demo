package middleware

import (
	"testing"

	"app/common/utils"
)

func newMiddlewareTestLogger(t *testing.T) *utils.ZeroLogger {
	t.Helper()
	logger, err := utils.NewZeroLogger(t.TempDir())
	if err != nil {
		t.Fatalf("创建测试日志器失败: %v", err)
	}
	t.Cleanup(func() {
		if err := logger.Close(); err != nil {
			t.Errorf("关闭测试日志器失败: %v", err)
		}
	})
	return logger
}

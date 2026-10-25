package testkit

import (
	"testing"

	"app/common/utils"
)

// NewTestLogger 创建写入临时目录的日志器，并在测试结束时自动关闭
func NewTestLogger(t *testing.T) *utils.ZeroLogger {
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

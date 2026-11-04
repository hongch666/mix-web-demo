package boot

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"app/common/constants"
	"app/common/utils"
	"app/internal/config"

	"github.com/zeromicro/go-zero/rest"
)

// 启动信息应写入传入的日志实例，不额外创建独立的日志文件句柄
func TestPrintStartupInfoReusesProvidedLogger(t *testing.T) {
	logDir := t.TempDir()
	logger, err := utils.NewZeroLogger(logDir, false)
	if err != nil {
		t.Fatalf("创建测试日志实例失败: %v", err)
	}
	t.Cleanup(func() {
		if closeErr := logger.Close(); closeErr != nil {
			t.Logf("关闭测试日志实例失败: %v", closeErr)
		}
	})

	PrintStartupInfo(newStartupTestConfig(), logger)

	logFile := filepath.Join(logDir, fmt.Sprintf("app_%s.log", time.Now().Format("2006-01-02")))
	content, err := os.ReadFile(logFile)
	if err != nil {
		t.Fatalf("读取启动日志失败: %v", err)
	}
	if !strings.Contains(string(content), constants.SERVER_START_SUCCESS) {
		t.Fatalf("启动日志缺少启动成功信息: %s", content)
	}
	if !strings.Contains(string(content), "127.0.0.1") {
		t.Fatalf("启动日志缺少服务地址: %s", content)
	}
}

// 未提供日志实例时降级到全局 logx，不 panic
func TestPrintStartupInfoFallsBackToLogx(t *testing.T) {
	PrintStartupInfo(newStartupTestConfig(), nil)
}

// newStartupTestConfig 构造启动信息打印所需的最小配置，Mode 为提升字段需单独赋值
func newStartupTestConfig() config.Config {
	cfg := config.Config{
		RestConf: rest.RestConf{Host: "127.0.0.1", Port: 8888},
	}
	cfg.Mode = "dev"
	return cfg
}

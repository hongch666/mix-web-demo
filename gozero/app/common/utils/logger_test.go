package utils

import (
	"context"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"go.opentelemetry.io/otel/trace"
)

// 验证该测试场景的预期行为

func TestZeroLoggerFileContainsTraceID(t *testing.T) {
	traceID := trace.TraceID{1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16}
	spanID := trace.SpanID{1, 2, 3, 4, 5, 6, 7, 8}
	spanContext := trace.NewSpanContext(trace.SpanContextConfig{
		TraceID:    traceID,
		SpanID:     spanID,
		TraceFlags: trace.FlagsSampled,
	})
	ctx := trace.ContextWithSpanContext(context.Background(), spanContext)
	logger, err := NewZeroLogger(t.TempDir())
	if err != nil {
		t.Fatalf("创建日志实例失败: %v", err)
	}
	requestLogger := logger.WithContext(ctx)
	t.Cleanup(func() {
		if closeErr := requestLogger.Close(); closeErr != nil {
			t.Errorf("关闭日志文件失败: %v", closeErr)
		}
	})

	requestLogger.Info("链路日志")
	logFile := filepath.Join(requestLogger.logPath, "app_"+time.Now().Format("2006-01-02")+".log")
	content, err := os.ReadFile(logFile)
	if err != nil {
		t.Fatalf("读取日志文件失败: %v", err)
	}

	if !strings.Contains(string(content), "trace_id="+traceID.String()) {
		t.Fatalf("日志未包含 trace_id: %s", content)
	}
}

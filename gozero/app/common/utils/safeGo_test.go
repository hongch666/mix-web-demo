package utils

import (
	"strings"
	"testing"
	"time"
)

type safeGoTestLogger struct{ message chan string }

func (l *safeGoTestLogger) Error(message string) { l.message <- message }

// 验证该测试场景的预期行为

func TestSafeGoRecoversPanicAndLogsTaskName(t *testing.T) {
	logger := &safeGoTestLogger{message: make(chan string, 1)}
	SafeGo(logger, "sync-task", func() { panic("boom") })
	select {
	case message := <-logger.message:
		if !strings.Contains(message, "sync-task") || !strings.Contains(message, "boom") {
			t.Fatalf("unexpected panic log: %s", message)
		}
	case <-time.After(time.Second):
		t.Fatal("panic was not recovered and logged")
	}
}

// 验证该测试场景的预期行为

func TestSafeGoRunsNormalTask(t *testing.T) {
	done := make(chan struct{})
	SafeGo(nil, "normal-task", func() { close(done) })
	select {
	case <-done:
	case <-time.After(time.Second):
		t.Fatal("normal task did not run")
	}
}

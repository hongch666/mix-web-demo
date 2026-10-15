package boot

import (
	"context"
	"testing"

	"app/internal/config"
	"app/internal/svc"
)

// 定时任务开关关闭时不注册本地调度器，也不触碰任何基础设施
func TestRegisterTaskSchedulerSkipsWhenDisabled(t *testing.T) {
	ctx := &svc.ServiceContext{
		RuntimeContext: &svc.RuntimeContext{},
		LoggerContext:  &svc.LoggerContext{},
	}

	registerTaskScheduler(config.Config{Task: config.TaskConfig{Enabled: false}}, ctx)

	if ctx.TaskScheduler != nil {
		t.Fatal("定时任务开关关闭时不应注册调度器")
	}
}

// 定时任务开关开启时注册调度器，由调用方在测试结束时停止
func TestRegisterTaskSchedulerRegistersWhenEnabled(t *testing.T) {
	ctx := &svc.ServiceContext{
		RuntimeContext: &svc.RuntimeContext{Context: context.Background()},
		LoggerContext:  &svc.LoggerContext{},
	}

	registerTaskScheduler(config.Config{Task: config.TaskConfig{Enabled: true}}, ctx)

	if ctx.TaskScheduler == nil {
		t.Fatal("定时任务开关开启时应注册调度器")
	}
	// cron 的 Stop 返回等待用的上下文，这里无需等待运行中的任务
	t.Cleanup(func() {
		ctx.TaskScheduler.Stop()
	})
}

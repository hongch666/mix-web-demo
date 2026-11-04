package svc

import (
	"testing"

	"github.com/robfig/cron/v3"
)

// RegisterTaskScheduler 应在 RuntimeContext 存在时写入调度器，由 Close 统一停止
func TestRegisterTaskSchedulerStoresScheduler(t *testing.T) {
	scheduler := cron.New()
	ctx := &ServiceContext{RuntimeContext: &RuntimeContext{}}

	ctx.RegisterTaskScheduler(scheduler)

	if ctx.RuntimeContext.TaskScheduler != scheduler {
		t.Fatal("调度器未注册到 RuntimeContext")
	}
	ctx.Close()
}

// 空上下文注册调度器必须静默忽略，避免半填充的测试上下文 panic
func TestRegisterTaskSchedulerIgnoresNilRuntimeContext(t *testing.T) {
	ctx := &ServiceContext{}
	ctx.RegisterTaskScheduler(cron.New())

	var nilCtx *ServiceContext
	nilCtx.RegisterTaskScheduler(cron.New())

	if ctx.RuntimeContext != nil && ctx.RuntimeContext.TaskScheduler != nil {
		t.Fatal("缺少 RuntimeContext 时不应注册调度器")
	}
}

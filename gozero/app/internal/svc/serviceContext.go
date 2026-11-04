// Code scaffolded by goctl. Safe to edit.

package svc

import (
	"context"

	"app/common/constants"
	"app/common/utils"
	"app/internal/config"

	"github.com/robfig/cron/v3"
	"github.com/zeromicro/go-zero/core/logx"
)

// ServiceContext 聚合各业务边界的服务依赖，通过匿名嵌入保持原有字段访问方式不变
type ServiceContext struct {
	*RuntimeContext
	*InfrastructureContext
	*ModelContext
	*HubContext
	*ClientContext
	*LoggerContext
	*MiddlewareContext
}

// NewServiceContext 初始化日志与内部令牌工具，装配基础设施、模型、Hub 等各分域依赖并构造服务上下文
func NewServiceContext(c config.Config) *ServiceContext {
	serviceContext, cancel := context.WithCancel(context.Background())

	// 初始化日志
	zLogger, err := utils.NewZeroLogger(c.Logs.Path, c.Logs.TimestampEnabled())
	if err != nil {
		logx.Errorf(constants.ZERO_LOGGER_INIT_FAIL, err)
		panic(err)
	}

	tokenUtil, err := utils.NewInternalTokenUtil(c.InternalToken.Secret, c.InternalToken.Expiration)
	if err != nil {
		logx.Errorf(constants.INTERNAL_TOKEN_INIT_FAIL, err)
		panic(err)
	}

	infrastructure := newInfrastructureContext(c, zLogger)
	// 装配后立即校验依赖清单：必需依赖缺失直接 panic，避免带病启动
	validateDependencies(infrastructure)
	clientCtx := newClientContext(infrastructure.NamingClient, c.RemoteCall, zLogger, tokenUtil, infrastructure.RedisClient)
	models := newModelContext(c, infrastructure, clientCtx, zLogger)

	serviceCtx := &ServiceContext{
		RuntimeContext:        &RuntimeContext{Context: serviceContext, Cancel: cancel, Config: c},
		InfrastructureContext: infrastructure,
		ModelContext:          models,
		HubContext:            newHubContext(zLogger),
		ClientContext:         clientCtx,
		LoggerContext:         newLoggerContext(zLogger),
		MiddlewareContext:     newMiddlewareContext(zLogger, clientCtx.SpringClient, tokenUtil),
	}
	if models.ChatMessagesModel != nil {
		serviceCtx.ChatHub.ConfigureReadMarker(models.ChatMessagesModel.MarkChatHistoryAsReadThrough)
	}

	// 实时通信组件组装到 HubContext 分域
	setupRealtime(serviceContext, serviceCtx.HubContext, infrastructure.RedisClient, zLogger)

	return serviceCtx
}

// RegisterTaskScheduler 注册定时任务调度器，装配在启动层完成，生命周期统一由 Close 释放
// task 包依赖 svc，不能由 svc 反向 import，因此创建仍在 boot 层，但不再从包外直接写字段
func (sc *ServiceContext) RegisterTaskScheduler(scheduler *cron.Cron) {
	if sc == nil || sc.RuntimeContext == nil {
		return
	}
	sc.RuntimeContext.TaskScheduler = scheduler
}

// Close 释放 ServiceContext 持有的所有资源
func (sc *ServiceContext) Close() {
	if sc == nil {
		return
	}
	if sc.RuntimeContext != nil && sc.RuntimeContext.TaskScheduler != nil {
		sc.RuntimeContext.TaskScheduler.Stop()
	}
	if sc.RuntimeContext != nil && sc.Cancel != nil {
		sc.Cancel()
	}
	if sc.HubContext != nil && sc.HubContext.RealtimeBus != nil {
		sc.HubContext.RealtimeBus.Close()
	}
	if sc.ClientContext != nil {
		sc.ClientContext.Close()
	}
	if sc.InfrastructureContext != nil {
		sc.InfrastructureContext.Close()
	}
	if sc.LoggerContext != nil {
		sc.LoggerContext.Close()
	}
}

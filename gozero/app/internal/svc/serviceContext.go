// Code scaffolded by goctl. Safe to edit.

package svc

import (
	"context"

	"app/common/constants"
	"app/common/utils"
	"app/internal/config"

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

	if err := utils.InitInternalTokenUtil(c.InternalToken.Secret, c.InternalToken.Expiration); err != nil {
		logx.Errorf(constants.INTERNAL_TOKEN_INIT_FAIL, err)
		panic(err)
	}

	infrastructure := newInfrastructureContext(c, zLogger)
	// 装配后立即校验依赖清单：必需依赖缺失直接 panic，避免带病启动
	validateDependencies(infrastructure)
	clientCtx := newClientContext(infrastructure.NamingClient, c.RemoteCall, zLogger)
	models := newModelContext(c, infrastructure, clientCtx, zLogger)

	serviceCtx := &ServiceContext{
		RuntimeContext:        &RuntimeContext{Context: serviceContext, Cancel: cancel, Config: c},
		InfrastructureContext: infrastructure,
		ModelContext:          models,
		HubContext:            newHubContext(zLogger),
		ClientContext:         clientCtx,
		LoggerContext:         newLoggerContext(zLogger),
		MiddlewareContext:     newMiddlewareContext(zLogger, clientCtx.SpringClient),
	}
	if models.ChatMessagesModel != nil {
		serviceCtx.ChatHub.ConfigureReadMarker(models.ChatMessagesModel.MarkChatHistoryAsReadThrough)
	}

	// 实时通信组件组装到 HubContext 分域
	setupRealtime(serviceContext, serviceCtx.HubContext, infrastructure.RedisClient, zLogger)

	return serviceCtx
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

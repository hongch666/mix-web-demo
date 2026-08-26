// Code scaffolded by goctl. Safe to edit.
// goctl 1.9.2

package svc

import (
	"context"

	"app/common/constants"
	"app/common/realtime"
	"app/common/utils"
	"app/internal/config"

	"github.com/zeromicro/go-zero/core/logx"
)

// ServiceContext 聚合各业务边界的服务依赖，通过匿名嵌入保持原有字段访问方式不变。
type ServiceContext struct {
	*RuntimeContext
	*InfrastructureContext
	*ModelContext
	*HubContext
	*ClientContext
	*LoggerContext
	*MiddlewareContext
	RealtimeBus        *realtime.RedisPubSub
	RealtimeDispatcher *realtime.ChatRealtimeDispatcher
}

func NewServiceContext(c config.Config) *ServiceContext {
	serviceContext, cancel := context.WithCancel(context.Background())

	// 初始化日志
	zLogger, err := utils.NewZeroLogger(c.Logs.Path)
	if err != nil {
		logx.Errorf(constants.ZERO_LOGGER_INIT_FAIL, err)
		panic(err)
	}

	if err := utils.InitInternalTokenUtil(c.InternalToken.Secret, c.InternalToken.Expiration); err != nil {
		logx.Errorf(constants.INTERNAL_TOKEN_INIT_FAIL, err)
		panic(err)
	}

	infrastructure := newInfrastructureContext(c, zLogger)
	clientCtx := newClientContext(infrastructure.NamingClient, c.RemoteCall)
	models := newModelContext(c, infrastructure, clientCtx)

	serviceCtx := &ServiceContext{
		RuntimeContext:        &RuntimeContext{Context: serviceContext, Cancel: cancel, Config: c},
		InfrastructureContext: infrastructure,
		ModelContext:          models,
		HubContext:            newHubContext(zLogger),
		ClientContext:         clientCtx,
		LoggerContext:         newLoggerContext(zLogger),
		MiddlewareContext:     newMiddlewareContext(zLogger),
	}
	serviceCtx.RealtimeDispatcher = realtime.NewChatRealtimeDispatcher(
		serviceContext,
		serviceCtx.ChatHub,
		serviceCtx.SSEHub,
		serviceCtx.ChatMessagesModel,
		zLogger,
	)

	if infrastructure.RedisClient != nil {
		serviceCtx.RealtimeBus = realtime.NewRedisPubSub(infrastructure.RedisClient, zLogger)
		serviceCtx.RealtimeBus.Start(serviceContext, serviceCtx.RealtimeDispatcher.Handle)
	}

	return serviceCtx
}

// Close 释放 ServiceContext 持有的所有资源
func (sc *ServiceContext) Close() {
	if sc == nil {
		return
	}
	if sc.RuntimeContext != nil && sc.Cancel != nil {
		sc.Cancel()
	}
	if sc.RealtimeBus != nil {
		sc.RealtimeBus.Close()
	}
	if sc.InfrastructureContext != nil {
		sc.InfrastructureContext.Close()
	}
	if sc.LoggerContext != nil {
		sc.LoggerContext.Close()
	}
}

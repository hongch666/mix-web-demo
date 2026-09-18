package svc

import (
	"context"
	"time"

	"app/common/client"
	"app/common/constants"
	"app/common/pubsub"
	"app/common/utils"
	"app/internal/client/fastapiClient"
	"app/internal/client/nestjsClient"
	"app/internal/client/springClient"
	"app/internal/config"
	"app/internal/hub"
	"app/internal/middleware"

	"github.com/nacos-group/nacos-sdk-go/v2/clients/naming_client"
	"github.com/redis/go-redis/v9"
	"github.com/zeromicro/go-zero/core/logx"
)

// 创建 HubContext 实例，初始化各业务 Hub 依赖
func newHubContext(zLogger *utils.ZeroLogger) *HubContext {
	sseHub := hub.GetSSEHub()
	sseHub.ZeroLogger = zLogger

	return &HubContext{
		ChatHub: &hub.ChatHub{ZeroLogger: zLogger},
		SSEHub:  sseHub,
	}
}

// 创建 ClientContext 实例，初始化各业务客户端依赖
func newClientContext(
	namingClient naming_client.INamingClient,
	remoteCallConfig config.RemoteCallConfig,
	zLogger *utils.ZeroLogger,
) *ClientContext {
	remoteCallCfg := client.RemoteCallConfig{
		Timeout:        time.Duration(remoteCallConfig.Timeout) * time.Millisecond,
		MaxRetries:     remoteCallConfig.MaxRetries,
		InitialBackoff: time.Duration(remoteCallConfig.InitialBackoff) * time.Millisecond,
		MaxBackoff:     time.Duration(remoteCallConfig.MaxBackoff) * time.Millisecond,
	}
	return &ClientContext{
		FastapiClient: fastapiClient.NewFastapiClient(namingClient, remoteCallCfg, zLogger),
		NestjsClient:  nestjsClient.NewNestjsClient(namingClient, remoteCallCfg, zLogger),
		SpringClient:  springClient.NewSpringClient(namingClient, remoteCallCfg, zLogger),
	}
}

// 创建 MiddlewareContext 实例，初始化服务级中间件依赖
func newMiddlewareContext(
	zLogger *utils.ZeroLogger,
	adminChecker middleware.AdminChecker,
) *MiddlewareContext {
	return &MiddlewareContext{
		UserContextMiddleware:     middleware.NewUserContextMiddleware().Handle,
		AllowSelfMiddleware:       middleware.NewAllowSelfMiddleware(adminChecker, zLogger).Handle,
		RecoveryMiddleware:        middleware.NewRecoveryMiddleware(zLogger).Handle,
		InternalServiceMiddleware: middleware.NewInternalServiceMiddleware(zLogger).Handle,
	}
}

// 创建 LoggerContext 实例，初始化服务级日志依赖
func newLoggerContext(zLogger *utils.ZeroLogger) *LoggerContext {
	return &LoggerContext{Logger: zLogger}
}

// resourceCloser 持有连接资源、需要随服务生命周期释放的客户端
type resourceCloser interface {
	Close()
}

// Close 释放三个远程客户端持有的连接池
// FastapiClient 字段是业务契约接口（测试用 mock 实现），生命周期方法不并入该接口，故此处按需断言
func (cc *ClientContext) Close() {
	if cc == nil {
		return
	}

	if closer, ok := cc.FastapiClient.(resourceCloser); ok {
		closer.Close()
	}
	if cc.NestjsClient != nil {
		cc.NestjsClient.Close()
	}
	if cc.SpringClient != nil {
		cc.SpringClient.Close()
	}
}

// Close 关闭日志文件句柄
func (lc *LoggerContext) Close() {
	if lc == nil || lc.Logger == nil {
		return
	}
	if err := lc.Logger.Close(); err != nil {
		logx.Errorf(constants.LOGGER_CLOSE_FILE_ERROR, err)
	}
}

// 组装实时通信组件并挂载到 HubContext 分域（RealtimeBus/RealtimeDispatcher 属实时通信域）
func setupRealtime(
	serviceCtx context.Context,
	hubCtx *HubContext,
	redisClient *redis.Client,
	zLogger *utils.ZeroLogger,
) {
	hubCtx.RealtimeDispatcher = hub.NewChatRealtimeDispatcher(
		hubCtx.ChatHub,
		hubCtx.SSEHub,
		zLogger,
	)

	if redisClient != nil {
		hubCtx.RealtimeBus = pubsub.NewRedisPubSub(redisClient, zLogger, constants.REALTIME_CHAT_CHANNEL)
		hubCtx.RealtimeBus.Start(serviceCtx, hubCtx.RealtimeDispatcher.Handle)
	}
}

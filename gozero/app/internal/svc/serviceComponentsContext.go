package svc

import (
	"app/common/constants"
	"app/common/hub"
	"app/common/utils"
	"app/internal/client/fastapiClient"
	"app/internal/middleware"

	"github.com/nacos-group/nacos-sdk-go/v2/clients/naming_client"
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
func newClientContext(namingClient naming_client.INamingClient) *ClientContext {
	return &ClientContext{
		FastapiClient: fastapiClient.NewFastapiClient(namingClient),
	}
}

// 创建 MiddlewareContext 实例，初始化服务级中间件依赖
func newMiddlewareContext(zLogger *utils.ZeroLogger) *MiddlewareContext {
	return &MiddlewareContext{
		UserContextMiddleware:     middleware.NewUserContextMiddleware().Handle,
		RecoveryMiddleware:        middleware.NewRecoveryMiddleware(zLogger).Handle,
		InternalServiceMiddleware: middleware.NewInternalServiceMiddleware(zLogger).Handle,
	}
}

// 创建 LoggerContext 实例，初始化服务级日志依赖
func newLoggerContext(zLogger *utils.ZeroLogger) *LoggerContext {
	return &LoggerContext{Logger: zLogger}
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

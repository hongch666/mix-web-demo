// Code scaffolded by goctl. Safe to edit.
// goctl 1.9.2

package svc

import (
	"context"

	"app/common/constants"
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
	models := newModelContext(c, infrastructure)

	return &ServiceContext{
		RuntimeContext:        &RuntimeContext{Context: serviceContext, Cancel: cancel, Config: c},
		InfrastructureContext: infrastructure,
		ModelContext:          models,
		HubContext:            newHubContext(zLogger),
		ClientContext:         newClientContext(infrastructure.NamingClient),
		LoggerContext:         newLoggerContext(zLogger),
		MiddlewareContext:     newMiddlewareContext(zLogger),
	}
}

// Close 释放 ServiceContext 持有的所有资源。
func (sc *ServiceContext) Close() {
	if sc == nil {
		return
	}
	if sc.RuntimeContext != nil && sc.Cancel != nil {
		sc.Cancel()
	}
	if sc.InfrastructureContext != nil {
		sc.InfrastructureContext.Close()
	}
	if sc.LoggerContext != nil {
		sc.LoggerContext.Close()
	}
}

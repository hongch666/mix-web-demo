package boot

import (
	"app/internal/config"
	"app/internal/handler"
	"app/internal/svc"
	"app/internal/task"

	"github.com/zeromicro/go-zero/rest"

	_ "app/docs"
)

// CreateServer 创建并初始化 REST 服务器
func CreateServer(c config.Config, ctx *svc.ServiceContext) *rest.Server {
	server := rest.MustNewServer(c.RestConf)

	// 优先注册 Swagger 路由（在业务处理器之前）
	registerSwaggerRoute(server)

	// 注册所有业务处理器
	handler.RegisterHandlers(server, ctx)

	// 初始化任务调度器
	task.InitTaskScheduler(ctx)

	// 输出启动信息
	PrintStartupInfo(c)

	return server
}

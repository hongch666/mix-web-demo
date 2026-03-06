package boot

import (
	"app/common/task"
	"app/internal/config"
	"app/internal/handler"
	"app/internal/svc"
	"net/http"

	swaggerFiles "github.com/swaggo/files"
	"github.com/zeromicro/go-zero/rest"

	_ "app/docs"
)

// CreateServer 创建并初始化 REST 服务器
func CreateServer(c config.Config, ctx *svc.ServiceContext) *rest.Server {
	server := rest.MustNewServer(c.RestConf)

	// 注册所有业务处理器
	handler.RegisterHandlers(server, ctx)

	// 注册 Swagger 路由
	registerSwaggerRoute(server)

	// 初始化任务调度器
	task.InitTaskScheduler(ctx)

	// 输出启动信息
	PrintStartupInfo(c)

	return server
}

// registerSwaggerRoute 注册 Swagger 文档路由
func registerSwaggerRoute(server *rest.Server) {
	server.AddRoute(rest.Route{
		Method: http.MethodGet,
		Path:   "/swagger/*",
		Handler: func(w http.ResponseWriter, r *http.Request) {
			swaggerFiles.Handler.ServeHTTP(w, r)
		},
	})
}

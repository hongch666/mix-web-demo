package boot

import (
	"fmt"

	"app/common/constants"
	"app/common/validation"
	"app/internal/config"
	"app/internal/handler"
	"app/internal/svc"
	"app/internal/task"

	"github.com/zeromicro/go-zero/core/logx"
	"github.com/zeromicro/go-zero/rest"
)

// CreateServer 创建并初始化 REST 服务器
func CreateServer(c config.Config, ctx *svc.ServiceContext) *rest.Server {
	// 初始化日志配置
	if err := logx.SetUp(logx.LogConf{Mode: "console"}); err != nil {
		logx.Errorf(constants.GOZERO_LOG_SETUP_FAIL, err)
	}

	// 注册请求参数校验器，缺失会让 httpx.Parse 静默跳过全部校验
	if err := validation.InitValidator(); err != nil {
		panic(fmt.Sprintf(constants.VALIDATOR_INIT_FAIL, err))
	}

	server := rest.MustNewServer(c.RestConf)

	// 优先注册 Swagger 路由（在业务处理器之前）
	registerSwaggerRoute(server)

	// 注册所有业务处理器
	handler.RegisterHandlers(server, ctx)

	// 初始化任务调度器并挂到运行时上下文，生命周期随 ServiceContext 管理
	ctx.TaskScheduler = task.NewTaskScheduler(ctx)

	// 输出启动信息
	PrintStartupInfo(c)

	return server
}

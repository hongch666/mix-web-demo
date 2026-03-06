package main

import (
	"flag"

	"app/internal/boot"
	"app/internal/svc"
)

var configFile = flag.String("f", "etc/application.yaml", "the config file")

func main() {
	flag.Parse()
	// 加载配置（包含环境变量）
	cfg := boot.LoadConfig(*configFile)
	// 创建服务上下文
	ctx := svc.NewServiceContext(cfg)
	// 创建并初始化服务器（包含路由注册、Swagger、任务调度器、启动信息输出）
	server := boot.CreateServer(cfg, ctx)
	defer server.Stop()
	// 启动服务器
	server.Start()
}

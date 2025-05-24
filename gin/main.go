package main

import (
	"fmt"
	"gin_proj/config"
	"gin_proj/routes"
)

func main() {
	// 初始化设置
	config.Init()
	// 初始化路由
	r := routes.SetupRouter()
	addr := fmt.Sprintf(":%d", config.Config.Server.Port)
	r.Run(addr) // 启动服务器
}

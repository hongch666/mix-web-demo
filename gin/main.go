package main

import (
	"fmt"

	"github.com/hongch666/mix-web-demo/gin/api"
	"github.com/hongch666/mix-web-demo/gin/common/config"

	_ "github.com/hongch666/mix-web-demo/gin/docs"
)

func main() {
	// 初始化路由
	r := api.SetupRouter()
	// 获取服务信息
	addr := fmt.Sprintf(":%d", config.Config.Server.Port)
	// 启动服务器
	r.Run(addr)
}

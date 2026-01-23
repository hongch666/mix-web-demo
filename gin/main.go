// @title       Gin部分的Swagger文档集成
// @version     1.0.0
// @description 这是demo项目的Gin部分的Swagger文档集成
// @host        localhost:8082
// @BasePath    /

package main

import (
	"fmt"
	"gin_proj/api"
	"gin_proj/config"

	_ "gin_proj/docs"
)

func main() {
	// 初始化路由
	r := api.SetupRouter()
	// 获取服务信息
	port := config.Config.Server.Port
	addr := fmt.Sprintf(":%d", port)
	config.InitMessage()
	// 启动服务器
	r.Run(addr)
}

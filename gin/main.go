// @title       Gin部分的Swagger文档集成
// @version     1.0.0
// @description 这是demo项目的Gin部分的Swagger文档集成
// @host        localhost:8082
// @BasePath    /

package main

import (
	"fmt"

	"github.com/hongch666/mix-web-demo/gin/api"
	"github.com/hongch666/mix-web-demo/gin/config"

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

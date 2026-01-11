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
	"log"

	_ "gin_proj/docs"
)

func main() {
	// 初始化路由
	r := api.SetupRouter()
	// 输出启动信息和Swagger地址
	ip := config.Config.Server.Ip
	port := config.Config.Server.Port
	addr := fmt.Sprintf(":%d", port)
	log.Printf("Gin应用已启动")
	log.Printf("服务地址: http://%s:%d", ip, port)
	log.Printf("Swagger文档地址: http://%s:%d/swagger/index.html", ip, port)
	// 启动服务器
	r.Run(addr)
}

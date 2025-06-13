// @title       Gin部分的Swagger文档集成
// @version     1.0.0
// @description 这是demo项目的Gin部分的Swagger文档集成
// @host        localhost:8082
// @BasePath    /

package main

// TODO: 修改获取文章数据同步ES的方式

import (
	"fmt"
	"gin_proj/config"
	"gin_proj/routes"
	"gin_proj/task"

	swaggerFiles "github.com/swaggo/files"
	ginSwagger "github.com/swaggo/gin-swagger"

	_ "gin_proj/docs"
)

func main() {
	// 初始化设置
	config.Init()
	// 开启定时任务
	task.InitTasks()
	// 初始化路由
	r := routes.SetupRouter()
	// Swagger 路由
	r.GET("/swagger/*any", ginSwagger.WrapHandler(swaggerFiles.Handler))
	addr := fmt.Sprintf(":%d", config.Config.Server.Port)
	r.Run(addr) // 启动服务器
}

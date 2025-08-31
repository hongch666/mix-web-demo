// @title       Gin部分的Swagger文档集成
// @version     1.0.0
// @description 这是demo项目的Gin部分的Swagger文档集成
// @host        localhost:8082
// @BasePath    /

package main

import (
	"fmt"
	"gin_proj/api/routes"
	"gin_proj/common/migrate"
	"gin_proj/common/task"
	"gin_proj/config"
	"log"

	swaggerFiles "github.com/swaggo/files"
	ginSwagger "github.com/swaggo/gin-swagger"

	_ "gin_proj/docs"
)

func main() {
	// 初始化设置
	config.Init()
	// 自动建表
	migrate.InitMigrate()
	// 开启定时任务
	task.InitTasks()
	// 初始化路由
	r := routes.SetupRouter()
	// Swagger 路由
	r.GET("/swagger/*any", ginSwagger.WrapHandler(swaggerFiles.Handler))
	addr := fmt.Sprintf(":%d", config.Config.Server.Port)

	// 输出启动信息和Swagger地址
	log.Printf("Gin应用已启动")
	log.Printf("服务地址: http://%s:%d", config.Config.Server.Ip, config.Config.Server.Port)
	log.Printf("Swagger文档地址: http://%s:%d/swagger/index.html", config.Config.Server.Ip, config.Config.Server.Port)

	r.Run(addr) // 启动服务器
}

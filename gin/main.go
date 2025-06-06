// @title       Gin部分的Swagger文档集成
// @version     1.0.0
// @description 这是demo项目的Gin部分的Swagger文档集成
// @host        localhost:8082
// @BasePath    /

// TODO: 取消用户模块
// TODO: 修改同步的获取MySQL的文章表的方式，改成使用Spring部分的获取所有文章接口

package main

import (
	"fmt"
	"gin_proj/config"
	"gin_proj/routes"

	swaggerFiles "github.com/swaggo/files"
	ginSwagger "github.com/swaggo/gin-swagger"

	_ "gin_proj/docs" // ❗非常重要：别忘了这行
)

func main() {
	// 初始化设置
	config.Init()
	// 初始化路由
	r := routes.SetupRouter()
	// Swagger 路由
	r.GET("/swagger/*any", ginSwagger.WrapHandler(swaggerFiles.Handler))
	addr := fmt.Sprintf(":%d", config.Config.Server.Port)
	r.Run(addr) // 启动服务器
}

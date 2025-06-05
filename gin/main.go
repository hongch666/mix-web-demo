// @title       Gin部分的Swagger文档集成
// @version     1.0.0
// @description 这是demo项目的Gin部分的Swagger文档集成
// @host        localhost:8082
// @BasePath    /

// TODO: 增加对ES的使用,包括配置类配置
// TODO: 增加文章表（MySQL）
// TODO: 文章表数据导入ES
// TODO: 使用ES进行搜索文章优化
// TODO: 增加文章模块，取消用户模块
// TODO: 增加分页查询的处理和对应的类

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

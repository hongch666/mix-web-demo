package routes

import (
	"gin_proj/controller"

	"github.com/gin-gonic/gin"
)

// SetupRouter 初始化路由
func SetupRouter() *gin.Engine {
	r := gin.Default()

	testGroup := r.Group("/api_gin")
	{
		//测试路由
		testGroup.GET("/gin", controller.TestController)
		//spring测试路由
		testGroup.GET("/spring", controller.JavaController)
		//nestjs测试路由
		testGroup.GET("/nestjs", controller.NestjsController)
	}
	userGroup := r.Group("/users")
	{
		//查询路由
		userGroup.GET("/", controller.GetUsersController)
	}
	return r
}

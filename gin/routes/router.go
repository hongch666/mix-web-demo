package routes

import (
	"gin_proj/controller"

	"github.com/gin-gonic/gin"
)

// SetupRouter 初始化路由
func SetupRouter() *gin.Engine {
	r := gin.Default()

	// r.POST("/login", controller.LoginController)
	// r.GET("/testRedis", controller.GetRedisData)

	testGroup := r.Group("/api_gin")
	// protected.Use(jwtMiddleware())
	{
		//测试路由
		testGroup.GET("/gin", controller.TestController)
		//spring测试路由
		testGroup.GET("/spring", controller.JavaController)
		//nestjs测试路由
		testGroup.GET("/nestjs", controller.NestjsController)
	}
	return r
}

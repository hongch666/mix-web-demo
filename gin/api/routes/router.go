package routes

import (
	"gin_proj/api/controller"
	"gin_proj/common/middleware"

	"github.com/gin-gonic/gin"
)

// SetupRouter 初始化路由
func SetupRouter() *gin.Engine {
	r := gin.Default()
	//注册中间件
	r.Use(middleware.InjectUserContext())
	r.Use(middleware.RecoveryMiddleware())

	testGroup := r.Group("/api_gin")
	{
		//测试路由
		testGroup.GET("/gin", controller.TestController)
		//spring测试路由
		testGroup.GET("/spring", controller.SpringController)
		//nestjs测试路由
		testGroup.GET("/nestjs", controller.NestjsController)
		//fastapi测试路由
		testGroup.GET("/fastapi", controller.FastapiController)
		//测试ES同步MySQL
		testGroup.POST("/syncer", controller.SyncES)
	}
	searchGroup := r.Group("/search")
	{
		//搜索文章
		searchGroup.GET("/", controller.SearchArticlesController)
	}
	return r
}

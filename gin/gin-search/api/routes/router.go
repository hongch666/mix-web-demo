package routes

import (
	"search/api/controller"
	"search/common/middleware"

	"github.com/gin-gonic/gin"
)

// SetupRouter 初始化路由
func SetupRouter() *gin.Engine {
	r := gin.Default()
	//注册中间件
	r.Use(middleware.InjectUserContext())
	r.Use(middleware.RecoveryMiddleware())

	// controller 注入
	searchController := controller.Group.SearchController
	testController := controller.Group.TestController

	testGroup := r.Group("/api_gin")
	{
		//测试ES同步MySQL
		testGroup.POST("/syncer", middleware.ApiLogMiddleware("测试同步ES"), testController.SyncES)
	}
	searchGroup := r.Group("/search")
	{
		//搜索文章
		searchGroup.GET("/", middleware.ApiLogMiddleware("搜索文章"), searchController.SearchArticlesController)
	}
	return r
}

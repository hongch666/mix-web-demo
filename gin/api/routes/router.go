package routes

import (
	"gin_proj/api/controller"
	"gin_proj/common/middleware"

	"github.com/gin-gonic/gin"

	swaggerFiles "github.com/swaggo/files"
	ginSwagger "github.com/swaggo/gin-swagger"
)

// SetupRouter 初始化路由
func SetupRouter() *gin.Engine {
	r := gin.Default()
	//注册中间件
	r.Use(middleware.InjectUserContext())
	r.Use(middleware.RecoveryMiddleware())

	// Swagger 路由
	r.GET("/swagger/*any", ginSwagger.WrapHandler(swaggerFiles.Handler))

	// controller 注入
	searchController := controller.Group.SearchController
	testController := controller.Group.TestController
	chatController := controller.Group.ChatController

	testGroup := r.Group("/api_gin")
	{
		//测试路由
		testGroup.GET("/gin", middleware.ApiLogMiddleware("测试Gin服务"), testController.TestController)
		//spring测试路由
		testGroup.GET("/spring", middleware.ApiLogMiddleware("测试Spring服务"), testController.SpringController)
		//nestjs测试路由
		testGroup.GET("/nestjs", middleware.ApiLogMiddleware("测试NestJS服务"), testController.NestjsController)
		//fastapi测试路由
		testGroup.GET("/fastapi", middleware.ApiLogMiddleware("测试FastAPI服务"), testController.FastapiController)
		//测试ES同步MySQL
		testGroup.POST("/syncer", middleware.ApiLogMiddleware("手动触发同步ES任务"), testController.SyncES)
	}
	searchGroup := r.Group("/search")
	{
		//搜索文章
		searchGroup.GET("/", middleware.ApiLogMiddleware("搜索文章"), searchController.SearchArticlesController)
	}

	// 聊天相关路由
	chatGroup := r.Group("/user-chat")
	{
		// 发送消息
		chatGroup.POST("/send", middleware.ApiLogMiddleware("发送消息"), chatController.SendMessage)
		// 获取聊天历史
		chatGroup.POST("/history", middleware.ApiLogMiddleware("获取聊天历史"), chatController.GetChatHistory)
		// 获取队列状态
		chatGroup.GET("/queue", middleware.ApiLogMiddleware("获取队列状态"), chatController.GetQueueStatus)
		// 手动加入队列
		chatGroup.POST("/join", middleware.ApiLogMiddleware("加入队列"), chatController.JoinQueue)
		// 手动离开队列
		chatGroup.POST("/leave", middleware.ApiLogMiddleware("离开队列"), chatController.LeaveQueue)
	}

	// WebSocket路由
	r.GET("/ws/chat", middleware.ApiLogMiddleware("WebSocket连接"), chatController.WebSocketHandler)

	return r
}

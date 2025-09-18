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

	// 静态文件服务（用于测试页面）
	r.Static("/static", "./static")

	// controller 注入
	searchController := controller.Group.SearchController
	testController := controller.Group.TestController
	chatController := controller.Group.ChatController

	testGroup := r.Group("/api_gin")
	{
		//测试路由
		testGroup.GET("/gin", testController.TestController)
		//spring测试路由
		testGroup.GET("/spring", testController.SpringController)
		//nestjs测试路由
		testGroup.GET("/nestjs", testController.NestjsController)
		//fastapi测试路由
		testGroup.GET("/fastapi", testController.FastapiController)
		//测试ES同步MySQL
		testGroup.POST("/syncer", testController.SyncES)
	}
	searchGroup := r.Group("/search")
	{
		//搜索文章
		searchGroup.GET("/", searchController.SearchArticlesController)
	}

	// 聊天相关路由
	chatGroup := r.Group("/user-chat")
	{
		// 发送消息
		chatGroup.POST("/send", chatController.SendMessage)
		// 获取聊天历史
		chatGroup.POST("/history", chatController.GetChatHistory)
		// 获取队列状态
		chatGroup.GET("/queue", chatController.GetQueueStatus)
		// 手动加入队列
		chatGroup.POST("/join", chatController.JoinQueue)
		// 手动离开队列
		chatGroup.POST("/leave", chatController.LeaveQueue)
	}

	// WebSocket路由
	r.GET("/ws/chat", chatController.WebSocketHandler)

	return r
}

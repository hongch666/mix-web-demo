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
	// 聊天相关路由
	chatGroup := r.Group("/user-chat")
	{
		// 发送消息
		chatGroup.POST("/send", controller.SendMessage)
		// 获取聊天历史
		chatGroup.POST("/history", controller.GetChatHistory)
		// 获取队列状态
		chatGroup.GET("/queue", controller.GetQueueStatus)
		// 手动加入队列
		chatGroup.POST("/join", controller.JoinQueue)
		// 手动离开队列
		chatGroup.POST("/leave", controller.LeaveQueue)
	}
	// WebSocket路由
	r.GET("/ws/chat", controller.WebSocketHandler)
	return r
}

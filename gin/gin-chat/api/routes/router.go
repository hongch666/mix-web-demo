package routes

import (
	"chat/api/controller"
	"chat/common/middleware"

	"github.com/gin-gonic/gin"
)

// SetupRouter 初始化路由
func SetupRouter() *gin.Engine {
	r := gin.Default()
	//注册中间件
	r.Use(middleware.InjectUserContext())
	r.Use(middleware.RecoveryMiddleware())

	chatController := controller.Group.ChatController
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

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

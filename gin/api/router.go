// @title       Gin部分的Swagger文档
// @version     1.0.0
// @description 这是项目的Gin部分的Swagger文档
// @host        localhost:8082
// @BasePath    /

package api

import (
	"github.com/hongch666/mix-web-demo/gin/api/controller"
	"github.com/hongch666/mix-web-demo/gin/common/config"
	"github.com/hongch666/mix-web-demo/gin/common/middleware"
	"github.com/hongch666/mix-web-demo/gin/common/utils"

	"github.com/gin-gonic/gin"

	swaggerFiles "github.com/swaggo/files"
	ginSwagger "github.com/swaggo/gin-swagger"
)

// SetupRouter 初始化路由
func SetupRouter() *gin.Engine {
	// 初始化内部服务令牌工具
	utils.InitInternalTokenUtil(config.Config.InternalToken.Secret, config.Config.InternalToken.Expiration)

	r := gin.Default()
	//注册中间件
	r.Use(middleware.InjectUserContext())
	r.Use(middleware.RecoveryMiddleware())

	// Swagger 路由
	r.GET("/swagger/*any", ginSwagger.WrapHandler(swaggerFiles.Handler))

	// 从 controller group 中获取控制器
	testController := controller.Group.TestController
	searchController := controller.Group.SearchController
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
		//测试ES同步MySQL - 需要内部令牌验证
		testGroup.POST("/syncer", middleware.RequireInternalToken(), middleware.ApiLogMiddleware("手动触发同步ES任务"), testController.SyncES)
	}
	searchGroup := r.Group("/search")
	{
		//搜索文章
		searchGroup.GET("/", middleware.ApiLogMiddleware("搜索文章"), searchController.SearchArticlesController)
		//获取搜索历史
		searchGroup.GET("/history/:userId", middleware.ApiLogMiddleware("获取搜索历史"), searchController.GetSearchHistoryController)
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
		// 获取两个用户间的未读消息数
		chatGroup.POST("/unread-count", middleware.ApiLogMiddleware("获取未读消息数"), chatController.GetUnreadCount)
		// 获取用户的所有未读消息数
		chatGroup.POST("/all-unread-counts", middleware.ApiLogMiddleware("获取所有未读消息数"), chatController.GetAllUnreadCounts)
	}

	// SSE连接路由
	r.GET("/sse/chat", middleware.ApiLogMiddleware("SSE连接"), chatController.SSEHandler)

	// WebSocket路由
	r.GET("/ws/chat", middleware.ApiLogMiddleware("WebSocket连接"), chatController.WebSocketHandler)

	return r
}

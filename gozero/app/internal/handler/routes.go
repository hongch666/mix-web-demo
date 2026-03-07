// @title GoZero部分的Swagger文档
// @description 这是项目的GoZero部分的Swagger文档
// @version 1.0.0
// @host localhost:8082
// @basePath /

package handler

import (
	"net/http"

	chat "app/internal/handler/chat"
	search "app/internal/handler/search"
	test "app/internal/handler/test"
	"app/internal/svc"

	"github.com/zeromicro/go-zero/rest"
)

func RegisterHandlers(server *rest.Server, serverCtx *svc.ServiceContext) {
	server.AddRoutes(
		rest.WithMiddlewares(
			[]rest.Middleware{serverCtx.UserContextMiddleware, serverCtx.RecoveryMiddleware},
			[]rest.Route{}...,
		),
	)

	server.AddRoutes(
		[]rest.Route{
			{
				// 获取所有未读消息数
				Method:  http.MethodPost,
				Path:    "/all-unread-counts",
				Handler: chat.ChatGetAllUnreadCountsHandler(serverCtx),
			},
			{
				// 获取聊天历史
				Method:  http.MethodPost,
				Path:    "/history",
				Handler: chat.ChatGetHistoryHandler(serverCtx),
			},
			{
				// 加入队列
				Method:  http.MethodPost,
				Path:    "/join",
				Handler: chat.ChatJoinQueueHandler(serverCtx),
			},
			{
				// 离开队列
				Method:  http.MethodPost,
				Path:    "/leave",
				Handler: chat.ChatLeaveQueueHandler(serverCtx),
			},
			{
				// 获取队列状态
				Method:  http.MethodGet,
				Path:    "/queue",
				Handler: chat.ChatGetQueueStatusHandler(serverCtx),
			},
			{
				// 发送消息
				Method:  http.MethodPost,
				Path:    "/send",
				Handler: chat.ChatSendMessageHandler(serverCtx),
			},
			{
				// 获取未读消息数
				Method:  http.MethodPost,
				Path:    "/unread-count",
				Handler: chat.ChatGetUnreadCountHandler(serverCtx),
			},
		},
		rest.WithPrefix("/user-chat"),
	)

	server.AddRoutes(
		[]rest.Route{
			{
				// SSE连接
				Method:  http.MethodGet,
				Path:    "/sse/chat",
				Handler: chat.ChatSSEHandler(serverCtx),
			},
			{
				// WebSocket连接
				Method:  http.MethodGet,
				Path:    "/ws/chat",
				Handler: chat.ChatWebsocketHandler(serverCtx),
			},
		},
	)

	server.AddRoutes(
		[]rest.Route{
			{
				// 搜索文章
				Method:  http.MethodGet,
				Path:    "/",
				Handler: search.SearchArticlesHandler(serverCtx),
			},
			{
				// 获取搜索历史
				Method:  http.MethodGet,
				Path:    "/history/:userId",
				Handler: search.GetSearchHistoryHandler(serverCtx),
			},
		},
		rest.WithPrefix("/search"),
	)

	server.AddRoutes(
		[]rest.Route{
			{
				// 测试FastAPI服务
				Method:  http.MethodGet,
				Path:    "/fastapi",
				Handler: test.TestFastAPIHandler(serverCtx),
			},
			{
				// 测试GoZero服务
				Method:  http.MethodGet,
				Path:    "/gozero",
				Handler: test.TestGoZeroHandler(serverCtx),
			},
			{
				// 测试NestJS服务
				Method:  http.MethodGet,
				Path:    "/nestjs",
				Handler: test.TestNestJSHandler(serverCtx),
			},
			{
				// 测试Spring服务
				Method:  http.MethodGet,
				Path:    "/spring",
				Handler: test.TestSpringHandler(serverCtx),
			},
		},
		rest.WithPrefix("/api_gozero"),
	)

	server.AddRoutes(
		rest.WithMiddlewares(
			[]rest.Middleware{serverCtx.InternalServiceMiddleware},
			[]rest.Route{
				{
					// 手动触发同步ES任务
					Method:  http.MethodPost,
					Path:    "/syncer",
					Handler: test.SyncESHandler(serverCtx),
				},
			}...,
		),
		rest.WithPrefix("/api_gozero"),
	)
}

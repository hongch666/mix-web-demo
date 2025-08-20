package controller

import (
	"gin_proj/api/service"
	"gin_proj/common/utils"
	"gin_proj/entity/dto"
	"net/http"

	"github.com/gin-gonic/gin"
	"github.com/gorilla/websocket"
)

var upgrader = websocket.Upgrader{
	CheckOrigin: func(r *http.Request) bool {
		return true // 生产环境需要验证Origin
	},
}

// SendMessage 发送消息接口
// @Summary 发送聊天消息
// @Description 发送聊天消息，先保存到数据库，再通过WebSocket发送给在线用户
// @Tags 聊天
// @Accept json
// @Produce json
// @Param request body dto.SendMessageRequest true "发送消息请求"
// @Success 200 {object} dto.SendMessageResponse
// @Router /user-chat/send [post]
func SendMessage(ctx *gin.Context) {
	var req dto.SendMessageRequest
	if err := ctx.ShouldBindJSON(&req); err != nil {
		utils.RespondError(ctx, http.StatusBadRequest, "参数错误: "+err.Error())
		return
	}

	response, err := service.SendChatMessage(&req)
	if err != nil {
		utils.RespondError(ctx, http.StatusInternalServerError, "发送消息失败: "+err.Error())
		return
	}

	utils.RespondSuccess(ctx, response)
}

// GetChatHistory 获取聊天历史记录
// @Summary 获取聊天历史记录
// @Description 获取两个用户之间的聊天历史记录
// @Tags 聊天
// @Accept json
// @Produce json
// @Param request body dto.GetChatHistoryRequest true "获取聊天历史请求"
// @Success 200 {object} dto.GetChatHistoryResponse
// @Router /user-chat/history [post]
func GetChatHistory(ctx *gin.Context) {
	var req dto.GetChatHistoryRequest
	if err := ctx.ShouldBindJSON(&req); err != nil {
		utils.RespondError(ctx, http.StatusBadRequest, "参数错误: "+err.Error())
		return
	}

	response, err := service.GetChatHistory(&req)
	if err != nil {
		utils.RespondError(ctx, http.StatusInternalServerError, "获取聊天历史失败: "+err.Error())
		return
	}

	utils.RespondSuccess(ctx, response)
}

// GetQueueStatus 获取队列状态
// @Summary 获取队列状态
// @Description 获取当前在队列中的所有用户
// @Tags 聊天
// @Produce json
// @Success 200 {object} dto.QueueStatusResponse
// @Router /user-chat/queue [get]
func GetQueueStatus(ctx *gin.Context) {
	response := service.GetQueueStatus()
	utils.RespondSuccess(ctx, response)
}

// JoinQueue 手动加入队列
// @Summary 手动加入聊天队列
// @Description 用户手动加入聊天队列，不需要建立WebSocket连接
// @Tags 聊天
// @Accept json
// @Produce json
// @Param request body dto.JoinQueueRequest true "加入队列请求"
// @Success 200 {object} dto.JoinQueueResponse
// @Router /user-chat/join [post]
func JoinQueue(ctx *gin.Context) {
	var req dto.JoinQueueRequest
	if err := ctx.ShouldBindJSON(&req); err != nil {
		utils.RespondError(ctx, http.StatusBadRequest, "参数错误: "+err.Error())
		return
	}

	response := service.JoinQueueManually(&req)
	utils.RespondSuccess(ctx, response)
}

// LeaveQueue 手动离开队列
// @Summary 手动离开聊天队列
// @Description 用户手动离开聊天队列
// @Tags 聊天
// @Accept json
// @Produce json
// @Param request body dto.LeaveQueueRequest true "离开队列请求"
// @Success 200 {object} dto.LeaveQueueResponse
// @Router /user-chat/leave [post]
func LeaveQueue(ctx *gin.Context) {
	var req dto.LeaveQueueRequest
	if err := ctx.ShouldBindJSON(&req); err != nil {
		utils.RespondError(ctx, http.StatusBadRequest, "参数错误: "+err.Error())
		return
	}

	response := service.LeaveQueueManually(&req)
	utils.RespondSuccess(ctx, response)
}

// WebSocketHandler WebSocket连接处理
// @Summary WebSocket聊天连接
// @Description 建立WebSocket连接，自动加入聊天队列
// @Tags 聊天
// @Param userId query string true "用户ID"
// @Router /ws/chat [get]
func WebSocketHandler(ctx *gin.Context) {
	userID := ctx.Query("userId")
	if userID == "" {
		// 尝试从Header获取（网关传递的用户信息）
		userID = ctx.GetHeader("X-User-Id")
	}

	if userID == "" {
		utils.RespondError(ctx, http.StatusBadRequest, "缺少用户ID")
		return
	}

	conn, err := upgrader.Upgrade(ctx.Writer, ctx.Request, nil)
	if err != nil {
		utils.RespondError(ctx, http.StatusInternalServerError, "WebSocket连接失败: "+err.Error())
		return
	}

	// 检查用户是否已经在队列中
	if existingClient, exists := service.GetUserFromQueue(userID); exists {
		// 用户已在队列中，更新其WebSocket连接
		existingClient.Conn = conn
		existingClient.Send = make(chan []byte, 256)
	} else {
		// 创建新的客户端并加入队列
		client := &service.Client{
			UserID: userID,
			Conn:   conn,
			Send:   make(chan []byte, 256),
		}
		service.JoinQueue(userID, client)
	}

	// 获取更新后的客户端
	client, _ := service.GetUserFromQueue(userID)

	// 启动读写协程
	go client.WritePump()
	go client.ReadPump()
}

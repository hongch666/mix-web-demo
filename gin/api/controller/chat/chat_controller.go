package chat

import (
	"gin_proj/api/service"
	"gin_proj/api/service/chat"
	"gin_proj/common/utils"
	"gin_proj/entity/dto"
	"net/http"

	"github.com/gin-gonic/gin"
	"github.com/gorilla/websocket"
)

// WebSocket相关校验，目前使用网关校验，这里直接放行
var upgrader = websocket.Upgrader{
	CheckOrigin: func(r *http.Request) bool {
		return true
	},
}

type ChatController struct{}

// SendMessage 发送消息接口
// @Summary 发送聊天消息
// @Description 发送聊天消息，先保存到数据库，再通过WebSocket发送给在线用户
// @Tags 聊天
// @Accept json
// @Produce json
// @Param request body dto.SendMessageRequest true "发送消息请求"
// @Success 200 {object} dto.SendMessageResponse
// @Router /user-chat/send [post]
func (con *ChatController) SendMessage(c *gin.Context) {
	// service注入
	chatService := service.Group.ChatService
	var req dto.SendMessageRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		utils.RespondError(c, http.StatusBadRequest, "参数错误: "+err.Error())
		return
	}

	response := chatService.SendChatMessage(&req)

	utils.RespondSuccess(c, response)
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
func (con *ChatController) GetChatHistory(c *gin.Context) {
	// service注入
	chatService := service.Group.ChatService
	var req dto.GetChatHistoryRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		utils.RespondError(c, http.StatusBadRequest, "参数错误: "+err.Error())
		return
	}

	response := chatService.GetChatHistory(&req)

	utils.RespondSuccess(c, response)
}

// GetQueueStatus 获取队列状态
// @Summary 获取队列状态
// @Description 获取当前在队列中的所有用户
// @Tags 聊天
// @Produce json
// @Success 200 {object} dto.QueueStatusResponse
// @Router /user-chat/queue [get]
func (con *ChatController) GetQueueStatus(c *gin.Context) {
	// service注入
	chatService := service.Group.ChatService

	response := chatService.GetQueueStatus()
	utils.RespondSuccess(c, response)
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
func (con *ChatController) JoinQueue(c *gin.Context) {
	// service注入
	chatService := service.Group.ChatService
	var req dto.JoinQueueRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		utils.RespondError(c, http.StatusBadRequest, "参数错误: "+err.Error())
		return
	}

	response := chatService.JoinQueueManually(&req)
	utils.RespondSuccess(c, response)
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
func (con *ChatController) LeaveQueue(c *gin.Context) {
	// service注入
	chatService := service.Group.ChatService
	var req dto.LeaveQueueRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		utils.RespondError(c, http.StatusBadRequest, "参数错误: "+err.Error())
		return
	}

	response := chatService.LeaveQueueManually(&req)
	utils.RespondSuccess(c, response)
}

// WebSocketHandler WebSocket连接处理
// @Summary WebSocket聊天连接
// @Description 建立WebSocket连接，自动加入聊天队列
// @Tags 聊天
// @Param userId query string true "用户ID"
// @Router /ws/chat [get]
func (con *ChatController) WebSocketHandler(c *gin.Context) {
	// service注入
	chatHub := service.Group.ChatHub
	userID := c.Query("userId")
	if userID == "" {
		// 尝试从Header获取（网关传递的用户信息）
		userID = c.GetHeader("X-User-Id")
	}

	if userID == "" {
		utils.RespondError(c, http.StatusBadRequest, "缺少用户ID")
		return
	}

	conn, err := upgrader.Upgrade(c.Writer, c.Request, nil)
	if err != nil {
		utils.RespondError(c, http.StatusInternalServerError, "WebSocket连接失败: "+err.Error())
		return
	}

	// 检查用户是否已经在队列中
	if existingClient, exists := chatHub.GetUserFromQueue(userID); exists {
		// 用户已在队列中，更新其WebSocket连接
		existingClient.Conn = conn
		existingClient.Send = make(chan []byte, 256)
	} else {
		// 创建新的客户端并加入队列
		client := &chat.Client{
			UserID: userID,
			Conn:   conn,
			Send:   make(chan []byte, 256),
		}
		chatHub.JoinQueue(userID, client)
	}

	// 获取更新后的客户端
	client, _ := chatHub.GetUserFromQueue(userID)

	// 启动读写协程
	go client.WritePump()
	go client.ReadPump()
}

package chat

import (
	"io"
	"net/http"
	"time"

	"github.com/hongch666/mix-web-demo/gin/api/service/chat"
	"github.com/hongch666/mix-web-demo/gin/common/utils"
	"github.com/hongch666/mix-web-demo/gin/entity/dto"

	"github.com/gin-gonic/gin"
	"github.com/gorilla/websocket"
)

// WebSocket相关校验，目前使用网关校验，这里直接放行
var upgrader = websocket.Upgrader{
	CheckOrigin: func(r *http.Request) bool {
		return true
	},
}

type ChatController struct {
	ChatService chat.ChatService
	ChatHub     chat.ChatHub
	SSEHub      *chat.SSEHubManager
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
func (con *ChatController) SendMessage(c *gin.Context) {
	var req dto.SendMessageRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		utils.Log.Error(utils.PARAM_ERR + err.Error())
		utils.Error(c, http.StatusOK, utils.PARAM_ERR)
		return
	}

	response := con.ChatService.SendChatMessage(&req)

	utils.Success(c, response)
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
	var req dto.GetChatHistoryRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		utils.Log.Error(utils.PARAM_ERR + err.Error())
		utils.Error(c, http.StatusOK, utils.PARAM_ERR)
		return
	}

	response := con.ChatService.GetChatHistory(&req)
	utils.Success(c, response)
}

// GetQueueStatus 获取队列状态
// @Summary 获取队列状态
// @Description 获取当前在队列中的所有用户
// @Tags 聊天
// @Produce json
// @Success 200 {object} dto.QueueStatusResponse
// @Router /user-chat/queue [get]
func (con *ChatController) GetQueueStatus(c *gin.Context) {
	response := con.ChatService.GetQueueStatus()
	utils.Success(c, response)
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
	var req dto.JoinQueueRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		utils.Log.Error(utils.PARAM_ERR + err.Error())
		utils.Error(c, http.StatusOK, utils.PARAM_ERR)
		return
	}

	response := con.ChatService.JoinQueueManually(&req)
	utils.Success(c, response)
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
	var req dto.LeaveQueueRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		utils.Log.Error(utils.PARAM_ERR + err.Error())
		utils.Error(c, http.StatusOK, utils.PARAM_ERR)
		return
	}

	response := con.ChatService.LeaveQueueManually(&req)
	utils.Success(c, response)
}

// WebSocketHandler WebSocket连接处理
// @Summary WebSocket聊天连接
// @Description 建立WebSocket连接，自动加入聊天队列
// @Tags 聊天
// @Param userId query string true "用户ID"
// @Router /ws/chat [get]
func (con *ChatController) WebSocketHandler(c *gin.Context) {
	userID := c.Query("userId")
	if userID == "" {
		// 尝试从Header获取（网关传递的用户信息）
		userID = c.GetHeader("X-User-Id")
	}

	if userID == "" {
		utils.Log.Error(utils.USER_ID_LESS)
		utils.Error(c, http.StatusOK, utils.USER_ID_LESS)
		return
	}

	conn, err := upgrader.Upgrade(c.Writer, c.Request, nil)
	if err != nil {
		utils.Log.Error(utils.WS_CONNECT_FAIL + err.Error())
		utils.Error(c, http.StatusOK, utils.WS_CONNECT_FAIL)
		return
	}

	// 检查用户是否已经在队列中
	if existingClient, exists := con.ChatHub.GetUserFromQueue(userID); exists {
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
		con.ChatHub.JoinQueue(userID, client)
	}

	// 获取更新后的客户端
	client, _ := con.ChatHub.GetUserFromQueue(userID)

	// 启动读写协程
	go client.WritePump()
	go client.ReadPump()
}

// GetUnreadCount 获取两个用户间的未读消息数
// @Summary 获取两个用户间的未读消息数
// @Description 获取指定用户与另一个用户间的未读消息数
// @Tags 聊天
// @Accept json
// @Produce json
// @Param request body dto.GetUnreadCountRequest true "获取未读消息数请求"
// @Success 200 {object} dto.UnreadCountResponse
// @Router /user-chat/unread-count [post]
func (con *ChatController) GetUnreadCount(c *gin.Context) {
	var req dto.GetUnreadCountRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		utils.Log.Error(utils.PARAM_ERR + err.Error())
		utils.Error(c, http.StatusOK, utils.PARAM_ERR)
		return
	}

	response := con.ChatService.GetUnreadCount(&req)
	utils.Success(c, response)
}

// GetAllUnreadCounts 获取用户与其他所有人的未读消息数
// @Summary 获取用户的所有未读消息数
// @Description 获取指定用户与所有其他用户的未读消息数统计
// @Tags 聊天
// @Accept json
// @Produce json
// @Param request body dto.GetAllUnreadCountRequest true "获取所有未读消息数请求"
// @Success 200 {object} dto.AllUnreadCountResponse
// @Router /user-chat/all-unread-counts [post]
func (con *ChatController) GetAllUnreadCounts(c *gin.Context) {
	var req dto.GetAllUnreadCountRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		utils.Log.Error(utils.PARAM_ERR + err.Error())
		utils.Error(c, http.StatusOK, utils.PARAM_ERR)
		return
	}

	response := con.ChatService.GetAllUnreadCounts(&req)
	utils.Success(c, response)
}

// SSEHandler SSE长连接处理
// @Summary SSE消息通知连接
// @Description 建立SSE连接，用于接收实时消息通知
// @Tags 聊天
// @Param userId query string true "用户ID"
// @Router /sse/chat [get]
func (con *ChatController) SSEHandler(c *gin.Context) {
	userID := c.Query("userId")
	if userID == "" {
		// 尝试从Header获取（网关传递的用户信息）
		userID = c.GetHeader("X-User-Id")
	}

	if userID == "" {
		utils.Log.Error(utils.USER_ID_LESS)
		utils.Error(c, http.StatusOK, utils.USER_ID_LESS)
		return
	}

	// 设置SSE响应头
	c.Header("Content-Type", "text/event-stream")
	c.Header("Cache-Control", "no-cache")
	c.Header("Connection", "keep-alive")
	// 注意：不要在这里设置CORS头，Gateway已经统一处理了

	sendCh := make(chan any, 256)
	closeCh := make(chan bool)

	// 注册客户端
	con.SSEHub.RegisterClient(userID, sendCh, closeCh)
	defer con.SSEHub.UnregisterClient(userID)

	// 发送初始化连接消息
	initMessage := &dto.SSEMessageNotification{
		Type:         "connected",
		UserID:       userID,
		UnreadCounts: make(map[string]int64),
	}
	sseMessage := chat.FormatSSEMessage(initMessage)
	_, _ = c.Writer.Write([]byte(sseMessage))
	c.Writer.Flush()

	// 创建心跳定时器
	ticker := time.NewTicker(30 * time.Second)
	defer ticker.Stop()

	// 响应流
	c.Stream(func(w io.Writer) bool {
		select {
		case <-closeCh:
			return false
		case <-ticker.C:
			// 发送心跳消息
			heartbeat := utils.SSE_HEARTBEAT
			_, err := w.Write([]byte(heartbeat))
			if err != nil {
				utils.Log.Error(utils.SSE_HEARTBEAT_WRITE_FAIL + err.Error())
				return false
			}
			return true
		case notification := <-sendCh:
			// 发送SSE格式的消息
			sseMessage := chat.FormatSSEMessage(notification)
			// 如果格式化后消息为空,跳过此次发送
			if sseMessage == "" {
				utils.Log.Warning(utils.EMPTY_SSE)
				return true
			}
			_, err := w.Write([]byte(sseMessage))
			if err != nil {
				utils.Log.Error(utils.SSE_WRITE_FAIL + err.Error())
				return false
			}
			return true
		}
	})
}

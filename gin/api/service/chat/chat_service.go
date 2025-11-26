package chat

import (
	"encoding/json"
	"fmt"
	"gin_proj/api/mapper/chat"
	"gin_proj/common/utils"
	"gin_proj/entity/dto"
	"gin_proj/entity/po"
	"time"
)

type ChatService struct {
	ChatMessageMapper chat.ChatMessageMapper
}

// 发送消息（HTTP接口调用）
func (s *ChatService) SendChatMessage(req *dto.SendMessageRequest) *dto.SendMessageResponse {
	chatHub := &ChatHub{}

	// 1. 先保存到数据库
	message := &po.ChatMessage{
		SenderID:   req.SenderID,
		ReceiverID: req.ReceiverID,
		Content:    req.Content,
		CreatedAt:  time.Now(),
	}

	s.ChatMessageMapper.CreateChatMessage(message)

	// 2. 检查接收者是否在队列中，如果在就通过WebSocket发送
	if chatHub.IsUserInQueue(req.ReceiverID) {
		wsMessage := &dto.WebSocketMessage{
			Type:       "message",
			SenderID:   req.SenderID,
			ReceiverID: req.ReceiverID,
			Content:    req.Content,
			MessageID:  message.ID,
			Timestamp:  message.CreatedAt.Format("2006-01-02 15:04:05"),
		}

		messageBytes, _ := json.Marshal(wsMessage)
		if !chatHub.SendMessageToQueue(req.ReceiverID, messageBytes) {
			// 发送失败，用户可能刚离线，但消息已保存
			utils.FileLogger.Error(fmt.Sprintf("用户 %s 不在线，消息已保存到数据库", req.ReceiverID))
		}
	} else {
		utils.FileLogger.Error(fmt.Sprintf("用户 %s 不在队列中，消息已保存到数据库", req.ReceiverID))
	}

	// 3. 返回响应
	response := &dto.SendMessageResponse{
		MessageID: message.ID,
	}

	return response
}

// 获取聊天历史记录
func (s *ChatService) GetChatHistory(req *dto.GetChatHistoryRequest) *dto.GetChatHistoryResponse {
	// 设置默认分页参数
	if req.Page <= 0 {
		req.Page = 1
	}
	if req.Size <= 0 {
		req.Size = 20
	}

	offset := (req.Page - 1) * req.Size
	messages, total := s.ChatMessageMapper.GetChatHistory(req.UserID, req.OtherID, offset, req.Size)

	// 转换为DTO
	messageItems := make([]dto.ChatMessageItem, len(messages))
	for i, msg := range messages {
		messageItems[i] = dto.ChatMessageItem{
			ID:         msg.ID,
			SenderID:   msg.SenderID,
			ReceiverID: msg.ReceiverID,
			Content:    msg.Content,
			CreatedAt:  msg.CreatedAt.Format("2006-01-02 15:04:05"),
		}
	}

	response := &dto.GetChatHistoryResponse{
		Messages: messageItems,
		Total:    total,
	}

	return response
}

// 获取队列状态
func (s *ChatService) GetQueueStatus() *dto.QueueStatusResponse {
	chatHub := &ChatHub{}
	users := chatHub.GetAllUsersInQueue()
	return &dto.QueueStatusResponse{
		OnlineUsers: users,
		Count:       len(users),
	}
}

// 手动加入队列（不建立WebSocket连接）
func (s *ChatService) JoinQueueManually(req *dto.JoinQueueRequest) *dto.JoinQueueResponse {
	response := &dto.JoinQueueResponse{
		UserID: req.UserID,
	}
	response.Status = "joined"

	// 检查用户是否已经在队列中
	chatHub := &ChatHub{}
	if chatHub.IsUserInQueue(req.UserID) {
		response.Status = "already_in_queue"
	} else {
		// 创建一个虚拟的客户端（没有WebSocket连接）
		client := &Client{
			UserID: req.UserID,
			Conn:   nil, // 没有WebSocket连接
			Send:   make(chan []byte, 256),
		}
		chatHub.JoinQueue(req.UserID, client)
		response.Status = "joined"
	}

	return response
}

// 手动离开队列
func (s *ChatService) LeaveQueueManually(req *dto.LeaveQueueRequest) *dto.LeaveQueueResponse {
	response := &dto.LeaveQueueResponse{
		UserID: req.UserID,
	}
	// 检查用户是否在队列中
	chatHub := &ChatHub{}
	if chatHub.IsUserInQueue(req.UserID) {
		chatHub.LeaveQueue(req.UserID)
		response.Status = "left"
	} else {
		response.Status = "not_in_queue"
	}

	return response
}

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
	ChatHub           *ChatHub
	SSEHub            *SSEHubManager
}

// 发送消息（HTTP接口调用）
func (s *ChatService) SendChatMessage(req *dto.SendMessageRequest) *dto.SendMessageResponse {
	chatHub := s.ChatHub

	// 1. 先保存到数据库，根据接收者是否在线设置已读状态
	message := &po.ChatMessage{
		SenderID:   req.SenderID,
		ReceiverID: req.ReceiverID,
		Content:    req.Content,
		IsRead:     0, // 初始为未读
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
		if chatHub.SendMessageToQueue(req.ReceiverID, messageBytes) {
			// 发送成功，消息已读
			s.ChatMessageMapper.MarkAsRead(message.ID)
			utils.FileLogger.Info(fmt.Sprintf("消息 %d 通过WebSocket发送成功，已标记为已读", message.ID))
		} else {
			// 发送失败，用户可能刚离线，消息保持未读
			utils.FileLogger.Error(fmt.Sprintf("用户 %s 不在线，消息 %d 已保存为未读", req.ReceiverID, message.ID))
			// 触发SSE通知发送未读消息
			go s.notifyUnreadMessage(req.ReceiverID, req.SenderID, message)
		}
	} else {
		utils.FileLogger.Error(fmt.Sprintf("用户 %s 不在队列中，消息 %d 已保存为未读", req.ReceiverID, message.ID))
		// 触发SSE通知发送未读消息
		go s.notifyUnreadMessage(req.ReceiverID, req.SenderID, message)
	}

	// 3. 返回响应
	response := &dto.SendMessageResponse{
		MessageID: message.ID,
	}

	return response
}

// notifyUnreadMessage 通知用户有新的未读消息
func (s *ChatService) notifyUnreadMessage(userID, _ string, message *po.ChatMessage) {
	sseHub := s.SSEHub

	// 获取该用户的所有未读消息数
	unreadCounts := s.ChatMessageMapper.GetAllUnreadCounts(userID)

	notification := &dto.SSEMessageNotification{
		Type:         "message",
		UserID:       userID,
		UnreadCounts: unreadCounts,
		Message: &dto.ChatMessageItem{
			ID:         message.ID,
			SenderID:   message.SenderID,
			ReceiverID: message.ReceiverID,
			Content:    message.Content,
			IsRead:     message.IsRead,
			CreatedAt:  message.CreatedAt.Format("2006-01-02 15:04:05"),
		},
	}

	sseHub.SendNotificationToUser(userID, notification)
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

	// 将发给当前用户的消息标记为已读
	if err := s.ChatMessageMapper.MarkChatHistoryAsRead(req.UserID, req.OtherID); err != nil {
		utils.FileLogger.Error(fmt.Sprintf("标记聊天历史为已读失败: %v", err))
	}

	// 转换为DTO
	messageItems := make([]dto.ChatMessageItem, len(messages))
	for i, msg := range messages {
		messageItems[i] = dto.ChatMessageItem{
			ID:         msg.ID,
			SenderID:   msg.SenderID,
			ReceiverID: msg.ReceiverID,
			Content:    msg.Content,
			IsRead:     1, // 已读
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
	chatHub := s.ChatHub
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
	chatHub := s.ChatHub
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
	chatHub := s.ChatHub
	if chatHub.IsUserInQueue(req.UserID) {
		chatHub.LeaveQueue(req.UserID)
		response.Status = "left"
	} else {
		response.Status = "not_in_queue"
	}

	return response
}

// GetUnreadCount 获取两个用户间的未读消息数
func (s *ChatService) GetUnreadCount(req *dto.GetUnreadCountRequest) *dto.UnreadCountResponse {
	unreadCount := s.ChatMessageMapper.GetUnreadCount(req.UserID, req.OtherID)
	return &dto.UnreadCountResponse{
		UnreadCount: unreadCount,
	}
}

// GetAllUnreadCounts 获取用户与其他所有人的未读消息数
func (s *ChatService) GetAllUnreadCounts(req *dto.GetAllUnreadCountRequest) *dto.AllUnreadCountResponse {
	unreadCounts := s.ChatMessageMapper.GetAllUnreadCounts(req.UserID)
	return &dto.AllUnreadCountResponse{
		Data: unreadCounts,
	}
}

package service

import "chat/api/service/chat"

type ServiceGroup struct {
	ChatService chat.ChatService
	ChatHub     chat.ChatHub
}

var Group = new(ServiceGroup)

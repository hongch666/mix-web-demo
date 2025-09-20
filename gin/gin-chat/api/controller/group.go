package controller

import "chat/api/controller/chat"

type ControllerGroup struct {
	ChatController chat.ChatController
}

var Group = new(ControllerGroup)

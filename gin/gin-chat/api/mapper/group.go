package mapper

import "chat/api/mapper/chat"

type MapperGroup struct {
	ChatMessageMapper chat.ChatMessageMapper
}

var Group = new(MapperGroup)

package service

import (
	"gin_proj/api/mapper"
	chatpkg "gin_proj/api/service/chat"
	searchpkg "gin_proj/api/service/search"
	testpkg "gin_proj/api/service/test"
)

type ServiceGroup struct {
	SearchService searchpkg.SearchService
	ChatService   chatpkg.ChatService
	ChatHub       chatpkg.ChatHub
	SSEHub        *chatpkg.SSEHubManager
	TestService   testpkg.TestService
}

func NewServiceGroup() *ServiceGroup {
	return &ServiceGroup{
		SearchService: searchpkg.SearchService{
			SearchMapper: mapper.Group.SearchMapper,
		},
		ChatService: chatpkg.ChatService{
			ChatMessageMapper: mapper.Group.ChatMessageMapper,
			ChatHub:           &chatpkg.ChatHub{},
			SSEHub:            chatpkg.GetSSEHub(),
		},
		ChatHub:     chatpkg.ChatHub{},
		SSEHub:      chatpkg.GetSSEHub(),
		TestService: testpkg.TestService{},
	}
}

var Group = NewServiceGroup()

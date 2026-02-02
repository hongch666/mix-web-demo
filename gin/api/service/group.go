package service

import (
	"github.com/hongch666/mix-web-demo/gin/api/mapper"
	chatpkg "github.com/hongch666/mix-web-demo/gin/api/service/chat"
	searchpkg "github.com/hongch666/mix-web-demo/gin/api/service/search"
	testpkg "github.com/hongch666/mix-web-demo/gin/api/service/test"
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

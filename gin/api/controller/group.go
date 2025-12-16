package controller

import (
	chatpkg "gin_proj/api/controller/chat"
	searchpkg "gin_proj/api/controller/search"
	testpkg "gin_proj/api/controller/test"
	"gin_proj/api/service"
)

type ControllerGroup struct {
	SearchController searchpkg.SearchController
	TestController   testpkg.TestController
	ChatController   chatpkg.ChatController
}

func NewControllerGroup() *ControllerGroup {
	return &ControllerGroup{
		TestController: testpkg.TestController{
			TestService: service.Group.TestService,
		},
		SearchController: searchpkg.SearchController{
			SearchService: service.Group.SearchService,
		},
		ChatController: chatpkg.ChatController{
			ChatService: service.Group.ChatService,
			ChatHub:     service.Group.ChatHub,
			SSEHub:      service.Group.SSEHub,
		},
	}
}

var Group = NewControllerGroup()

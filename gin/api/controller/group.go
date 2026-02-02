package controller

import (
	chatpkg "github.com/hongch666/mix-web-demo/gin/api/controller/chat"
	searchpkg "github.com/hongch666/mix-web-demo/gin/api/controller/search"
	testpkg "github.com/hongch666/mix-web-demo/gin/api/controller/test"
	"github.com/hongch666/mix-web-demo/gin/api/service"
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

package controller

import (
	"gin_proj/api/controller/chat"
	"gin_proj/api/controller/search"
	"gin_proj/api/controller/test"
)

type ControllerGroup struct {
	SearchController search.SearchController
	TestController   test.TestController
	ChatController   chat.ChatController
}

var Group = new(ControllerGroup)

package service

import (
	"gin_proj/api/service/chat"
	"gin_proj/api/service/search"
	"gin_proj/api/service/test"
)

type ServiceGroup struct {
	SearchService search.SearchService
	ChatService   chat.ChatService
	ChatHub       chat.ChatHub
	TestService   test.TestService
}

var Group = new(ServiceGroup)

package service

type ServiceGroup struct {
	SearchService SearchService
	ChatService   ChatService
	ChatHub       ChatHub
	TestService   TestService
}

var Group = new(ServiceGroup)

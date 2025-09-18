package controller

type ControllerGroup struct {
	SearchController SearchController
	TestController   TestController
	ChatController   ChatController
}

var Group = new(ControllerGroup)

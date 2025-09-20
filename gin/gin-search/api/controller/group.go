package controller

import (
	"search/api/controller/search"
	"search/api/controller/test"
)

type ControllerGroup struct {
	SearchController search.SearchController
	TestController   test.TestController
}

var Group = new(ControllerGroup)

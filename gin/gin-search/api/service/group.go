package service

import "search/api/service/search"

type ServiceGroup struct {
	SearchService search.SearchService
}

var Group = new(ServiceGroup)

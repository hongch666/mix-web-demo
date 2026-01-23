package test

import (
	"gin_proj/common/client"
	"gin_proj/common/exceptions"
	"gin_proj/common/utils"
	"gin_proj/config"
	"net/http"

	"github.com/gin-gonic/gin"
)

type TestService struct{}

func (s *TestService) SpringService(c *gin.Context) any {
	opts := client.RequestOptions{
		Method: http.MethodGet,
	}
	sd := client.NewServiceDiscovery(config.NamingClient)
	result, err := sd.CallService(c, "spring", "/api_spring/spring", opts)
	if err != nil {
		panic(exceptions.NewBusinessError(utils.PARSE_ERR, err.Error()))
	}
	return result.Data
}

func (s *TestService) NestjsService(c *gin.Context) any {
	opts := client.RequestOptions{
		Method: http.MethodGet,
	}
	sd := client.NewServiceDiscovery(config.NamingClient)
	result, err := sd.CallService(c, "nestjs", "/api_nestjs/nestjs", opts)
	if err != nil {
		panic(exceptions.NewBusinessError(utils.PARSE_ERR, err.Error()))
	}
	return result.Data
}

func (s *TestService) FastapiService(c *gin.Context) any {
	opts := client.RequestOptions{
		Method: http.MethodGet,
	}
	sd := client.NewServiceDiscovery(config.NamingClient)
	result, err := sd.CallService(c, "fastapi", "/api_fastapi/fastapi", opts)
	if err != nil {
		panic(exceptions.NewBusinessError(utils.PARSE_ERR, err.Error()))
	}
	return result.Data
}

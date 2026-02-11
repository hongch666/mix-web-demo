package test

import (
	"net/http"

	"github.com/hongch666/mix-web-demo/gin/common/client"
	"github.com/hongch666/mix-web-demo/gin/common/config"
	"github.com/hongch666/mix-web-demo/gin/common/exceptions"
	"github.com/hongch666/mix-web-demo/gin/common/utils"

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

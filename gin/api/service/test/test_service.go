package test

import (
	"gin_proj/common/client"
	"gin_proj/config"
	"net/http"

	"github.com/gin-gonic/gin"
)

type TestService struct{}

func (s *TestService) SpringService(c *gin.Context) interface{} {
	opts := client.RequestOptions{
		Method: http.MethodGet,
		/* PathParams: map[string]string{"orderId": "789"},
		   QueryParams: url.Values{"version": []string{"2.0"}}, */
		/* BodyData: map[string]interface{}{
		    "status": "shipped",
		    "items": []int{101, 205},
		}, */
		/* Headers: map[string]string{
		    "X-Request-ID":  uuid.New().String(),
		    "Authorization": "Bearer xyz123",
		}, */
	}
	sd := client.NewServiceDiscovery(config.NamingClient)
	result, err := sd.CallService(c, "spring", "/api_spring/spring", opts)
	if err != nil {
		panic(err.Error())
	}
	return result.Data
}

func (s *TestService) NestjsService(c *gin.Context) interface{} {
	opts := client.RequestOptions{
		Method: http.MethodGet,
	}
	sd := client.NewServiceDiscovery(config.NamingClient)
	result, err := sd.CallService(c, "nestjs", "/api_nestjs/nestjs", opts)
	if err != nil {
		panic(err.Error())
	}
	return result.Data
}

func (s *TestService) FastapiService(c *gin.Context) interface{} {
	opts := client.RequestOptions{
		Method: http.MethodGet,
	}
	sd := client.NewServiceDiscovery(config.NamingClient)
	result, err := sd.CallService(c, "fastapi", "/api_fastapi/fastapi", opts)
	if err != nil {
		panic(err.Error())
	}
	return result.Data
}

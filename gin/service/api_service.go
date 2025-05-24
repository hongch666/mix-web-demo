package service

import (
	"gin_proj/client"
	"gin_proj/config"
	"net/http"

	"github.com/gin-gonic/gin"
)

func SpringService(c *gin.Context) (interface{}, error) {
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
		return nil, err
	}
	return result.Data, nil
}

func NestjsService(c *gin.Context) (interface{}, error) {
	opts := client.RequestOptions{
		Method: http.MethodGet,
	}
	sd := client.NewServiceDiscovery(config.NamingClient)
	result, err := sd.CallService(c, "nestjs", "/api_nestjs/nestjs", opts)
	if err != nil {
		return nil, err
	}
	return result.Data, nil
}

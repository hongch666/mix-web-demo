package springClient

import (
	"context"

	"app/common/client"

	"github.com/nacos-group/nacos-sdk-go/v2/clients/naming_client"
)

// SpringClient Spring 服务客户端
type SpringClient struct {
	serviceName  string
	namingClient naming_client.INamingClient
	serviceDisc  *client.ServiceDiscovery
}

// NewSpringClient 创建 Spring 客户端
func NewSpringClient(nc naming_client.INamingClient) *SpringClient {
	return &SpringClient{
		serviceName:  "spring",
		namingClient: nc,
		serviceDisc:  client.NewServiceDiscovery(nc),
	}
}

// Test 测试 Spring 服务连通性，返回完整响应结果
func (c *SpringClient) Test(ctx context.Context) (client.Result, error) {
	return c.serviceDisc.CallService(ctx, c.serviceName, "/api_spring/spring", client.RequestOptions{
		Method: "GET",
	})
}

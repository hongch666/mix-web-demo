package nestjsClient

import (
	"context"

	"app/common/client"

	"github.com/nacos-group/nacos-sdk-go/v2/clients/naming_client"
)

// NestjsClient NestJS 服务客户端
type NestjsClient struct {
	serviceName  string
	namingClient naming_client.INamingClient
	serviceDisc  *client.ServiceDiscovery
}

// NewNestjsClient 创建 NestJS 客户端
func NewNestjsClient(nc naming_client.INamingClient) *NestjsClient {
	return &NestjsClient{
		serviceName:  "nestjs",
		namingClient: nc,
		serviceDisc:  client.NewServiceDiscovery(nc),
	}
}

// Test 测试 NestJS 服务连通性，返回完整响应结果
func (c *NestjsClient) Test(ctx context.Context) (client.Result, error) {
	return c.serviceDisc.CallService(ctx, c.serviceName, "/api_nestjs/nestjs", client.RequestOptions{
		Method: "GET",
	})
}

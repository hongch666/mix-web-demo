package nestjsClient

import (
	"context"
	"encoding/json"
	"fmt"

	"app/common/client"

	"github.com/nacos-group/nacos-sdk-go/v2/clients/naming_client"
)

// NestjsClient NestJS 服务客户端
type NestjsClient struct {
	serviceName  string
	namingClient naming_client.INamingClient
}

// NewNestjsClient 创建 NestJS 客户端
func NewNestjsClient(nc naming_client.INamingClient) *NestjsClient {
	return &NestjsClient{
		serviceName:  "nestjs",
		namingClient: nc,
	}
}

// Test 测试 NestJS 服务连通性，返回完整响应结果
func (c *NestjsClient) Test(ctx context.Context) (client.Result, error) {
	sd := client.NewServiceDiscovery(c.namingClient)
	return sd.CallService(ctx, c.serviceName, "/api_nestjs/nestjs", client.RequestOptions{
		Method: "GET",
	})
}

func (c *NestjsClient) GetSearchHistory(ctx context.Context, userID int64) ([]string, error) {
	sd := client.NewServiceDiscovery(c.namingClient)
	result, err := sd.CallService(ctx, c.serviceName, fmt.Sprintf("/article-logs/search-history/%d", userID), client.RequestOptions{
		Method: "GET",
	})
	if err != nil {
		return nil, err
	}
	payload, err := json.Marshal(result.Data)
	if err != nil {
		return nil, err
	}
	var history SearchHistoryResponse
	if err := json.Unmarshal(payload, &history); err != nil {
		return nil, err
	}
	return history.Keywords, nil
}

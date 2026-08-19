package nestjsClient

import (
	"context"
	"strconv"

	"app/common/client"

	"github.com/nacos-group/nacos-sdk-go/v2/clients/naming_client"
)

// NestjsClient NestJS 服务客户端，提供搜索历史等内部数据查询能力
type NestjsClient struct {
	serviceName  string
	namingClient naming_client.INamingClient
	serviceDisc  *client.ServiceDiscovery
}

// NewNestjsClient 创建 NestJS 客户端
func NewNestjsClient(
	nc naming_client.INamingClient,
	remoteCallConfig client.RemoteCallConfig,
) *NestjsClient {
	return &NestjsClient{
		serviceName:  "nestjs",
		namingClient: nc,
		serviceDisc:  client.NewServiceDiscovery(nc, remoteCallConfig),
	}
}

// GetSearchHistory 调用 NestJS 内部接口获取用户搜索历史，返回完整响应结果
func (c *NestjsClient) GetSearchHistory(ctx context.Context, userID int64) (client.Result, error) {
	return c.serviceDisc.CallService(ctx, c.serviceName, "/article-logs/search-history/:user_id", client.RequestOptions{
		Method: "GET",
		PathParams: map[string]string{
			"user_id": strconv.FormatInt(userID, 10),
		},
	})
}

package springClient

import (
	"context"
	"encoding/json"
	"net/url"
	"strconv"

	"app/common/client"

	"github.com/nacos-group/nacos-sdk-go/v2/clients/naming_client"
)

// SpringClient Spring 服务客户端
type SpringClient struct {
	serviceName  string
	namingClient naming_client.INamingClient
}

// NewSpringClient 创建 Spring 客户端
func NewSpringClient(nc naming_client.INamingClient) *SpringClient {
	return &SpringClient{
		serviceName:  "spring",
		namingClient: nc,
	}
}

// Test 测试 Spring 服务连通性，返回完整响应结果
func (c *SpringClient) Test(ctx context.Context) (client.Result, error) {
	sd := client.NewServiceDiscovery(c.namingClient)
	return sd.CallService(ctx, c.serviceName, "/api_spring/spring", client.RequestOptions{
		Method: "GET",
	})
}

func (c *SpringClient) GetArticleSearchDocs(ctx context.Context, cursor int64, size int) (*ArticleSearchDocsPage, error) {
	sd := client.NewServiceDiscovery(c.namingClient)
	query := url.Values{}
	query.Set("cursor", strconv.FormatInt(cursor, 10))
	query.Set("size", strconv.Itoa(size))
	result, err := sd.CallService(ctx, c.serviceName, "/articles/search-docs", client.RequestOptions{
		Method:      "GET",
		QueryParams: query,
	})
	if err != nil {
		return nil, err
	}
	payload, err := json.Marshal(result.Data)
	if err != nil {
		return nil, err
	}
	var page ArticleSearchDocsPage
	if err := json.Unmarshal(payload, &page); err != nil {
		return nil, err
	}
	return &page, nil
}

func (c *SpringClient) GetArticleSearchStats(ctx context.Context, ids []int64) (map[int64]ArticleStatistic, error) {
	sd := client.NewServiceDiscovery(c.namingClient)
	result, err := sd.CallService(ctx, c.serviceName, "/articles/search-stats", client.RequestOptions{
		Method:   "POST",
		BodyData: map[string]any{"ids": ids},
	})
	if err != nil {
		return nil, err
	}
	payload, err := json.Marshal(result.Data)
	if err != nil {
		return nil, err
	}
	var raw map[string]ArticleStatistic
	if err := json.Unmarshal(payload, &raw); err != nil {
		return nil, err
	}
	stats := make(map[int64]ArticleStatistic, len(raw))
	for key, value := range raw {
		id, err := strconv.ParseInt(key, 10, 64)
		if err != nil {
			continue
		}
		stats[id] = value
	}
	return stats, nil
}

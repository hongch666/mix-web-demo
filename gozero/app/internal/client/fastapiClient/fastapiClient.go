package fastapiClient

import (
	"context"
	"errors"
	"fmt"

	"app/common/client"
	"app/common/utils"

	"github.com/nacos-group/nacos-sdk-go/v2/clients/naming_client"
)

// FastapiClient FastAPI 服务客户端，提供图谱搜索和向量搜索增强功能
type FastapiClient struct {
	serviceName  string
	namingClient naming_client.INamingClient
}

// NewFastapiClient 创建 FastAPI 客户端
func NewFastapiClient(nc naming_client.INamingClient) *FastapiClient {
	return &FastapiClient{
		serviceName:  "fastapi",
		namingClient: nc,
	}
}

// EnhanceGraph 调用 FastAPI 图谱增强接口，返回完整响应结果
func (c *FastapiClient) EnhanceGraph(ctx context.Context, req *GraphEnhanceRequest) (client.Result, error) {
	if len(req.ArticleIDs) == 0 {
		return client.Result{}, fmt.Errorf(utils.GRAPH_ENHANCE_CALL_FAILED, errors.New("文章ID列表为空"))
	}

	sd := client.NewServiceDiscovery(c.namingClient)
	return sd.CallService(ctx, c.serviceName, "/graph-search/enhance", client.RequestOptions{
		Method: "POST",
		BodyData: map[string]any{
			"user_id":           req.UserID,
			"keyword":           req.Keyword,
			"article_ids":       req.ArticleIDs,
			"category_name":     req.CategoryName,
			"sub_category_name": req.SubCategoryName,
			"tags":              req.Tags,
			"limit":             req.Limit,
			"mode":              req.Mode,
		},
	})
}

// EnhanceVector 调用 FastAPI 向量增强接口，返回完整响应结果
func (c *FastapiClient) EnhanceVector(ctx context.Context, req *VectorEnhanceRequest) (client.Result, error) {
	if len(req.ArticleIDs) == 0 || req.Keyword == "" {
		return client.Result{}, fmt.Errorf(utils.VECTOR_ENHANCE_CALL_FAILED, errors.New("文章ID列表为空或关键词为空"))
	}

	sd := client.NewServiceDiscovery(c.namingClient)
	return sd.CallService(ctx, c.serviceName, "/vector-search/enhance", client.RequestOptions{
		Method: "POST",
		BodyData: map[string]any{
			"user_id":           req.UserID,
			"keyword":           req.Keyword,
			"article_ids":       req.ArticleIDs,
			"category_name":     req.CategoryName,
			"sub_category_name": req.SubCategoryName,
			"tags":              req.Tags,
			"limit":             req.Limit,
			"top_k":             req.TopK,
			"mode":              req.Mode,
		},
	})
}

// Test 测试 FastAPI 服务连通性，返回完整响应结果
func (c *FastapiClient) Test(ctx context.Context) (client.Result, error) {
	sd := client.NewServiceDiscovery(c.namingClient)
	return sd.CallService(ctx, c.serviceName, "/api_fastapi/fastapi", client.RequestOptions{
		Method: "GET",
	})
}

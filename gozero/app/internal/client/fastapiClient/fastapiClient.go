package fastapiClient

import (
	"context"
	"errors"
	"fmt"
	"strconv"

	"app/common/client"
	"app/common/constants"
	"app/common/utils"

	"github.com/nacos-group/nacos-sdk-go/v2/clients/naming_client"
)

// FastapiClient FastAPI 服务客户端，提供图谱搜索和向量搜索增强功能
type FastapiClient struct {
	serviceName  string
	namingClient naming_client.INamingClient
	serviceDisc  *client.ServiceDiscovery
}

// NewFastapiClient 创建 FastAPI 客户端
func NewFastapiClient(
	nc naming_client.INamingClient,
	remoteCallConfig client.RemoteCallConfig,
	logger *utils.ZeroLogger,
) *FastapiClient {
	return &FastapiClient{
		serviceName:  "fastapi",
		namingClient: nc,
		serviceDisc:  client.NewServiceDiscovery(nc, remoteCallConfig, logger),
	}
}

// EnhanceGraph 调用 FastAPI 图谱增强接口，返回完整响应结果
func (c *FastapiClient) EnhanceGraph(ctx context.Context, req *GraphEnhanceRequest) (client.Result, error) {
	if len(req.ArticleIDs) == 0 {
		return client.Result{}, fmt.Errorf(constants.GRAPH_ENHANCE_CALL_FAILED, errors.New(constants.FASTAPI_ARTICLE_IDS_EMPTY))
	}

	sd := c.serviceDisc
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
		return client.Result{}, fmt.Errorf(constants.VECTOR_ENHANCE_CALL_FAILED, errors.New(constants.FASTAPI_ARTICLE_IDS_OR_KEYWORD_EMPTY))
	}

	sd := c.serviceDisc
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

// GetAiHistoryByID 根据ID查询AI历史记录
func (c *FastapiClient) GetAiHistoryByID(ctx context.Context, id int64) (client.Result, error) {
	return c.serviceDisc.CallService(ctx, c.serviceName, "/ai_history/internal/:id", client.RequestOptions{
		Method: "GET",
		PathParams: map[string]string{
			"id": strconv.FormatInt(id, 10),
		},
	})
}

// UpdateAiHistory 更新AI历史记录
func (c *FastapiClient) UpdateAiHistory(ctx context.Context, id int64, req *UpdateAiHistoryRequest) (client.Result, error) {
	return c.serviceDisc.CallService(ctx, c.serviceName, "/ai_history/internal/:id", client.RequestOptions{
		Method: "PUT",
		PathParams: map[string]string{
			"id": strconv.FormatInt(id, 10),
		},
		BodyData: req,
	})
}

// DeleteAiHistory 删除AI历史记录
func (c *FastapiClient) DeleteAiHistory(ctx context.Context, id int64) (client.Result, error) {
	return c.serviceDisc.CallService(ctx, c.serviceName, "/ai_history/internal/:id", client.RequestOptions{
		Method: "DELETE",
		PathParams: map[string]string{
			"id": strconv.FormatInt(id, 10),
		},
	})
}

package fastapiClient

import (
	"context"
	"errors"
	"fmt"

	"app/common/client"
	"app/common/constants"
	apptypes "app/internal/types"

	"github.com/nacos-group/nacos-sdk-go/v2/clients/naming_client"
)

// FastapiClient FastAPI 服务客户端，提供图谱搜索和向量搜索增强功能
type FastapiClient struct {
	serviceName  string
	namingClient naming_client.INamingClient
	serviceDisc  *client.ServiceDiscovery
}

// NewFastapiClient 创建 FastAPI 客户端
func NewFastapiClient(nc naming_client.INamingClient) *FastapiClient {
	return &FastapiClient{
		serviceName:  "fastapi",
		namingClient: nc,
		serviceDisc:  client.NewServiceDiscovery(nc),
	}
}

// EnhanceGraph 调用 FastAPI 图谱增强接口，返回完整响应结果
func (c *FastapiClient) EnhanceGraph(ctx context.Context, req *GraphEnhanceRequest) (client.Result, error) {
	if len(req.ArticleIDs) == 0 {
		return client.Result{}, fmt.Errorf(constants.GRAPH_ENHANCE_CALL_FAILED, errors.New("文章ID列表为空"))
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
		return client.Result{}, fmt.Errorf(constants.VECTOR_ENHANCE_CALL_FAILED, errors.New("文章ID列表为空或关键词为空"))
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

// Test 测试 FastAPI 服务连通性，返回完整响应结果
func (c *FastapiClient) Test(ctx context.Context) (client.Result, error) {
	sd := c.serviceDisc
	return sd.CallService(ctx, c.serviceName, "/api_fastapi/fastapi", client.RequestOptions{
		Method: "GET",
	})
}

// GetMatchedChunks 获取文章的匹配文本片段（仅用于展示，不参与排序）
func (c *FastapiClient) GetMatchedChunks(ctx context.Context, articleIDs []int64, keyword string) (map[int64][]apptypes.VectorMatchedChunk, error) {
	result, err := c.EnhanceVector(ctx, &VectorEnhanceRequest{
		Keyword:    keyword,
		ArticleIDs: articleIDs,
		Limit:      len(articleIDs),
		TopK:       len(articleIDs),
		Mode:       "hybrid",
	})
	if err != nil {
		return nil, err
	}

	items, err := ParseVectorEnhanceResult(result.Data)
	if err != nil {
		return nil, err
	}

	chunksMap := make(map[int64][]apptypes.VectorMatchedChunk, len(items))
	for _, item := range items {
		var chunks []apptypes.VectorMatchedChunk
		for _, c := range item.MatchedChunks {
			chunks = append(chunks, apptypes.VectorMatchedChunk{
				ArticleId:  c.ArticleID,
				Title:      c.Title,
				ChunkIndex: c.ChunkIndex,
				Score:      c.Score,
				Content:    c.Content,
			})
		}
		chunksMap[item.ArticleID] = chunks
	}
	return chunksMap, nil
}

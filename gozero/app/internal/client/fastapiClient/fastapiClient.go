package fastapiClient

import (
	"context"
	"errors"
	"fmt"

	"app/common/cache"
	"app/common/client"
	"app/common/constants"
	"app/common/redis"
	"app/common/utils"
	"app/model/search"

	"github.com/nacos-group/nacos-sdk-go/v2/clients/naming_client"
	goredis "github.com/redis/go-redis/v9"
)

// FastapiClient FastAPI 服务客户端，提供图谱搜索和向量搜索增强功能
type FastapiClient struct {
	serviceName  string
	namingClient naming_client.INamingClient
	serviceDisc  *client.ServiceDiscovery
	// 搜索算法配置的两级缓存，权重、脚本模板与脚本参数名映射变更频率低，跨实例共享 Redis 副本
	searchWeightsCache      *cache.MultiLevelCache[search.SearchWeights]
	searchScriptCache       *cache.MultiLevelCache[search.SearchScript]
	searchScriptParamsCache *cache.MultiLevelCache[search.ScriptParamMapping]
}

// NewFastapiClient 创建 FastAPI 客户端，redisClient 为 nil 时算法配置缓存退化为纯本地缓存
func NewFastapiClient(
	nc naming_client.INamingClient,
	remoteCallConfig client.RemoteCallConfig,
	logger *utils.ZeroLogger,
	tokenUtil *utils.InternalTokenUtil,
	redisClient *goredis.Client,
) *FastapiClient {
	cacheOptions := cache.Options{
		Store:  redis.NewCacheStore(redisClient),
		Logger: logger,
	}

	return &FastapiClient{
		serviceName:             "fastapi",
		namingClient:            nc,
		serviceDisc:             client.NewServiceDiscovery(nc, remoteCallConfig, logger, tokenUtil),
		searchWeightsCache:      cache.NewMultiLevelCache[search.SearchWeights](cacheOptions),
		searchScriptCache:       cache.NewMultiLevelCache[search.SearchScript](cacheOptions),
		searchScriptParamsCache: cache.NewMultiLevelCache[search.ScriptParamMapping](cacheOptions),
	}
}

// Close 释放客户端持有的远程调用连接
func (c *FastapiClient) Close() {
	if c == nil {
		return
	}

	c.serviceDisc.Close()
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

package springClient

import (
	"context"
	"strconv"

	"app/common/client"

	"github.com/nacos-group/nacos-sdk-go/v2/clients/naming_client"
)

// SpringClient Spring Boot 服务客户端，提供 MySQL 数据查询能力
type SpringClient struct {
	serviceName  string
	namingClient naming_client.INamingClient
	serviceDisc  *client.ServiceDiscovery
}

// NewSpringClient 创建 Spring 客户端
func NewSpringClient(
	nc naming_client.INamingClient,
	remoteCallConfig client.RemoteCallConfig,
) *SpringClient {
	return &SpringClient{
		serviceName:  "spring",
		namingClient: nc,
		serviceDisc:  client.NewServiceDiscovery(nc, remoteCallConfig),
	}
}

// GetPublishedArticles 分页获取已发布文章列表
func (c *SpringClient) GetPublishedArticles(ctx context.Context, page, size int) (client.Result, error) {
	return c.serviceDisc.CallService(ctx, c.serviceName, "/articles/list", client.RequestOptions{
		Method: "GET",
		QueryParams: map[string][]string{
			"page": {strconv.Itoa(page)},
			"size": {strconv.Itoa(size)},
		},
	})
}

// GetArticleViewsByIDs 批量查询文章阅读量
func (c *SpringClient) GetArticleViewsByIDs(ctx context.Context, ids []int64) (client.Result, error) {
	return c.serviceDisc.CallService(ctx, c.serviceName, "/articles/views/batch", client.RequestOptions{
		Method:   "POST",
		BodyData: map[string]any{"ids": ids},
	})
}

// GetArticlesByIDs 批量查询文章
func (c *SpringClient) GetArticlesByIDs(ctx context.Context, ids []int64) (client.Result, error) {
	return c.serviceDisc.CallService(ctx, c.serviceName, "/articles/batch", client.RequestOptions{
		Method:   "POST",
		BodyData: map[string]any{"ids": ids},
	})
}

// GetUserByID 根据ID查询用户
func (c *SpringClient) GetUserByID(ctx context.Context, id int64) (client.Result, error) {
	return c.serviceDisc.CallService(ctx, c.serviceName, "/users/:id", client.RequestOptions{
		Method: "GET",
		PathParams: map[string]string{
			"id": strconv.FormatInt(id, 10),
		},
	})
}

// GetUsersByIDs 批量查询用户
func (c *SpringClient) GetUsersByIDs(ctx context.Context, ids []int64) (client.Result, error) {
	return c.serviceDisc.CallService(ctx, c.serviceName, "/users/batch", client.RequestOptions{
		Method:   "POST",
		BodyData: map[string]any{"ids": ids},
	})
}

// GetCommentScoresByArticleIDs 批量查询评论评分（按角色分组）
func (c *SpringClient) GetCommentScoresByArticleIDs(ctx context.Context, ids []int64) (client.Result, error) {
	return c.serviceDisc.CallService(ctx, c.serviceName, "/comments/scores/batch", client.RequestOptions{
		Method:   "POST",
		BodyData: map[string]any{"ids": ids},
	})
}

// GetLikeCountsByArticleIDs 批量查询点赞数
func (c *SpringClient) GetLikeCountsByArticleIDs(ctx context.Context, ids []int64) (client.Result, error) {
	return c.serviceDisc.CallService(ctx, c.serviceName, "/likes/counts/batch", client.RequestOptions{
		Method:   "POST",
		BodyData: map[string]any{"ids": ids},
	})
}

// GetCollectCountsByArticleIDs 批量查询收藏数
func (c *SpringClient) GetCollectCountsByArticleIDs(ctx context.Context, ids []int64) (client.Result, error) {
	return c.serviceDisc.CallService(ctx, c.serviceName, "/collects/counts/batch", client.RequestOptions{
		Method:   "POST",
		BodyData: map[string]any{"ids": ids},
	})
}

// GetFollowCountsByUserIDs 批量查询粉丝数
func (c *SpringClient) GetFollowCountsByUserIDs(ctx context.Context, ids []int64) (client.Result, error) {
	return c.serviceDisc.CallService(ctx, c.serviceName, "/focus/counts/batch", client.RequestOptions{
		Method:   "POST",
		BodyData: map[string]any{"ids": ids},
	})
}

// GetCategoriesByIDs 批量查询分类
func (c *SpringClient) GetCategoriesByIDs(ctx context.Context, ids []int64) (client.Result, error) {
	return c.serviceDisc.CallService(ctx, c.serviceName, "/category/batch", client.RequestOptions{
		Method:   "POST",
		BodyData: map[string]any{"ids": ids},
	})
}

// GetSubCategoriesByIDs 批量查询子分类
func (c *SpringClient) GetSubCategoriesByIDs(ctx context.Context, ids []int64) (client.Result, error) {
	return c.serviceDisc.CallService(ctx, c.serviceName, "/category/sub/batch", client.RequestOptions{
		Method:   "POST",
		BodyData: map[string]any{"ids": ids},
	})
}

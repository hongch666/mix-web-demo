package nestjsClient

import (
	"context"

	"app/common/client"
)

// Client 定义 GoZero 使用的 NestJS 调用契约，便于业务层隔离远程依赖
type Client interface {
	GetSearchHistory(context.Context, int64) (client.Result, error)
}

// SearchHistoryResponse NestJS 返回的搜索历史响应
type SearchHistoryResponse struct {
	Keywords []string `json:"keywords"`
}

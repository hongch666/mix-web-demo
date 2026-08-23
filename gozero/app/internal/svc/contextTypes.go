package svc

import (
	"context"
	"database/sql"

	"app/common/hub"
	"app/common/utils"
	"app/internal/client/fastapiClient"
	"app/internal/client/nestjsClient"
	"app/internal/client/springClient"
	"app/internal/config"
	"app/model/chatMessages"
	"app/model/search"

	"github.com/nacos-group/nacos-sdk-go/v2/clients/naming_client"
	"github.com/olivere/elastic/v7"
	"github.com/redis/go-redis/v9"
	rabbitmq "github.com/wagslane/go-rabbitmq"
	"github.com/zeromicro/go-zero/core/stores/sqlx"
	"github.com/zeromicro/go-zero/rest"
)

// RuntimeContext 保存服务级生命周期和配置
type RuntimeContext struct {
	Context context.Context
	Cancel  context.CancelFunc
	Config  config.Config
}

// InfrastructureContext 保存数据库、消息队列和服务发现等基础设施依赖
type InfrastructureContext struct {
	MySQLConn         sqlx.SqlConn
	// RawMySQL 标准库 MySQL 连接，供动态列 SQL（如 SQL 工具）手动扫描结果。
	RawMySQL          *sql.DB
	ESClient          *elastic.Client
	RabbitMQPublisher *rabbitmq.Publisher
	RedisClient       *redis.Client
	NamingClient      naming_client.INamingClient
}

// ModelContext 保存业务模型依赖
type ModelContext struct {
	ChatMessagesModel chatMessages.ChatMessagesModel
	SearchModel       search.SearchModel
}

// HubContext 保存实时通信相关依赖
type HubContext struct {
	ChatHub *hub.ChatHub
	SSEHub  *hub.SSEHubManager
}

// ClientContext 保存内部服务客户端
type ClientContext struct {
	FastapiClient *fastapiClient.FastapiClient
	NestjsClient  *nestjsClient.NestjsClient
	SpringClient  *springClient.SpringClient
}

// LoggerContext 保存服务级日志依赖
type LoggerContext struct {
	Logger *utils.ZeroLogger
}

// MiddlewareContext 保存服务级中间件依赖
type MiddlewareContext struct {
	UserContextMiddleware     rest.Middleware
	RecoveryMiddleware        rest.Middleware
	InternalServiceMiddleware rest.Middleware
}

package svc

import (
	"context"

	"app/common/hub"
	"app/common/utils"
	"app/internal/client/fastapiClient"
	"app/internal/config"
	"app/model/aiHistory"
	"app/model/articles"
	"app/model/category"
	"app/model/categoryReference"
	"app/model/chatMessages"
	"app/model/collects"
	"app/model/comments"
	"app/model/focus"
	"app/model/likes"
	"app/model/search"
	"app/model/subCategory"
	"app/model/user"

	"github.com/nacos-group/nacos-sdk-go/v2/clients/naming_client"
	"github.com/olivere/elastic/v7"
	"github.com/redis/go-redis/v9"
	rabbitmq "github.com/wagslane/go-rabbitmq"
	"github.com/zeromicro/go-zero/core/stores/sqlx"
	"github.com/zeromicro/go-zero/rest"
	"go.mongodb.org/mongo-driver/mongo"
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
	ESClient          *elastic.Client
	RabbitMQPublisher *rabbitmq.Publisher
	MongoClient       *mongo.Client
	RedisClient       *redis.Client
	NamingClient      naming_client.INamingClient
}

// ModelContext 保存业务模型依赖
type ModelContext struct {
	AiHistoryModel         aiHistory.AiHistoryModel
	ArticlesModel          articles.ArticlesModel
	CategoryModel          category.CategoryModel
	CategoryReferenceModel categoryReference.CategoryReferenceModel
	ChatMessagesModel      chatMessages.ChatMessagesModel
	CollectsModel          collects.CollectsModel
	CommentsModel          comments.CommentsModel
	FocusModel             focus.FocusModel
	LikesModel             likes.LikesModel
	SubCategoryModel       subCategory.SubCategoryModel
	UserModel              user.UserModel
	SearchModel            search.SearchModel
}

// HubContext 保存实时通信相关依赖
type HubContext struct {
	ChatHub *hub.ChatHub
	SSEHub  *hub.SSEHubManager
}

// ClientContext 保存内部服务客户端
type ClientContext struct {
	FastapiClient *fastapiClient.FastapiClient
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

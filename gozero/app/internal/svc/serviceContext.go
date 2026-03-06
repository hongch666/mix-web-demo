// Code scaffolded by goctl. Safe to edit.
// goctl 1.9.2

package svc

import (
	"app/common/chat"
	"app/common/logger"
	"app/common/utils"
	"app/internal/config"
	"app/internal/middleware"
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
	"context"
	"fmt"
	"log"
	"os"
	"time"

	"github.com/nacos-group/nacos-sdk-go/v2/clients"
	"github.com/nacos-group/nacos-sdk-go/v2/clients/naming_client"
	"github.com/nacos-group/nacos-sdk-go/v2/common/constant"
	"github.com/nacos-group/nacos-sdk-go/v2/vo"
	"github.com/olivere/elastic/v7"
	amqp "github.com/rabbitmq/amqp091-go"
	"github.com/zeromicro/go-zero/core/stores/sqlx"
	"github.com/zeromicro/go-zero/rest"
	"go.mongodb.org/mongo-driver/mongo"
	"go.mongodb.org/mongo-driver/mongo/options"
	"gorm.io/driver/mysql"
	"gorm.io/gorm"
)

type ServiceContext struct {
	Config          config.Config
	MySQLConn       sqlx.SqlConn
	DB              *gorm.DB
	ESClient        *elastic.Client
	RabbitMQConn    *amqp.Connection
	RabbitMQChannel *amqp.Channel
	MongoClient     *mongo.Client
	NamingClient    naming_client.INamingClient

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

	ChatHub *chat.ChatHub
	SSEHub  *chat.SSEHubManager

	Logger *logger.ZeroLogger

	UserContextMiddleware     rest.Middleware
	RecoveryMiddleware        rest.Middleware
	InternalServiceMiddleware rest.Middleware
}

func NewServiceContext(c config.Config) *ServiceContext {
	// 初始化日志
	zLogger, err := logger.NewZeroLogger(c.Logs.Path)
	if err != nil {
		panic(err)
	}

	mysqlConn := initSqlx(c)
	db := initGorm(c)
	esClient := initES(c)
	rabbitConn, rabbitChannel := initRabbitMQ(c)
	mongoClient := initMongoDB(c)
	namingClient := initNacos(c)

	var (
		aiHistoryModel         aiHistory.AiHistoryModel
		articlesModel          articles.ArticlesModel
		categoryModel          category.CategoryModel
		categoryReferenceModel categoryReference.CategoryReferenceModel
		chatMessagesModel      chatMessages.ChatMessagesModel
		collectsModel          collects.CollectsModel
		commentsModel          comments.CommentsModel
		focusModel             focus.FocusModel
		likesModel             likes.LikesModel
		subCategoryModel       subCategory.SubCategoryModel
		userModel              user.UserModel
		searchModel            search.SearchModel
	)

	if db != nil {
		aiHistoryModel = aiHistory.NewAiHistoryModel(db)
		articlesModel = articles.NewArticlesModel(db)
		categoryModel = category.NewCategoryModel(db)
		categoryReferenceModel = categoryReference.NewCategoryReferenceModel(db)
		chatMessagesModel = chatMessages.NewChatMessagesModel(db)
		collectsModel = collects.NewCollectsModel(db)
		commentsModel = comments.NewCommentsModel(db)
		focusModel = focus.NewFocusModel(db)
		likesModel = likes.NewLikesModel(db)
		subCategoryModel = subCategory.NewSubCategoryModel(db)
		userModel = user.NewUserModel(db)
	}

	searchModel = search.NewSearchModel(search.SearchModelDeps{
		ESClient:      esClient,
		MongoClient:   mongoClient,
		MongoDatabase: c.Database.MongoDB.Database,
		Config: search.SearchModelConfig{
			ESScoreWeight:         c.Search.ESScoreWeight,
			AIRatingWeight:        c.Search.AIRatingWeight,
			UserRatingWeight:      c.Search.UserRatingWeight,
			ViewsWeight:           c.Search.ViewsWeight,
			LikesWeight:           c.Search.LikesWeight,
			CollectsWeight:        c.Search.CollectsWeight,
			AuthorFollowWeight:    c.Search.AuthorFollowWeight,
			RecencyWeight:         c.Search.RecencyWeight,
			MaxViewsNormalized:    c.Search.MaxViewsNormalized,
			MaxLikesNormalized:    c.Search.MaxLikesNormalized,
			MaxCollectsNormalized: c.Search.MaxCollectsNormalized,
			MaxFollowsNormalized:  c.Search.MaxFollowsNormalized,
			RecencyDecayDays:      c.Search.RecencyDecayDays,
		},
		ArticlesModel: articlesModel,
		LikesModel:    likesModel,
		CollectsModel: collectsModel,
		FocusModel:    focusModel,
	})

	return &ServiceContext{
		Config:                 c,
		MySQLConn:              mysqlConn,
		DB:                     db,
		ESClient:               esClient,
		RabbitMQConn:           rabbitConn,
		RabbitMQChannel:        rabbitChannel,
		MongoClient:            mongoClient,
		NamingClient:           namingClient,
		AiHistoryModel:         aiHistoryModel,
		ArticlesModel:          articlesModel,
		CategoryModel:          categoryModel,
		CategoryReferenceModel: categoryReferenceModel,
		ChatMessagesModel:      chatMessagesModel,
		CollectsModel:          collectsModel,
		CommentsModel:          commentsModel,
		FocusModel:             focusModel,
		LikesModel:             likesModel,
		SubCategoryModel:       subCategoryModel,
		UserModel:              userModel,
		SearchModel:            searchModel,
		ChatHub:                &chat.ChatHub{ZeroLogger: zLogger},
		SSEHub: func() *chat.SSEHubManager {
			hub := chat.GetSSEHub()
			hub.ZeroLogger = zLogger
			return hub
		}(),
		Logger:                    zLogger,
		UserContextMiddleware:     middleware.NewUserContextMiddleware().Handle,
		RecoveryMiddleware:        middleware.NewRecoveryMiddleware(zLogger).Handle,
		InternalServiceMiddleware: middleware.NewInternalServiceMiddleware().Handle,
	}
}

func initSqlx(c config.Config) sqlx.SqlConn {
	dsn := buildMysqlDsn(c)
	if dsn == "" {
		return nil
	}
	return sqlx.NewMysql(dsn)
}

func initGorm(c config.Config) *gorm.DB {
	dsn := buildMysqlDsn(c)
	if dsn == "" {
		return nil
	}

	db, err := gorm.Open(mysql.Open(dsn), &gorm.Config{})
	if err != nil {
		panic(err)
	}

	if sqlDB, err := db.DB(); err == nil {
		sqlDB.SetMaxIdleConns(10)
		sqlDB.SetMaxOpenConns(100)
		sqlDB.SetConnMaxLifetime(time.Hour)
	}

	initMigrate(db)

	return db
}

func initMigrate(db *gorm.DB) {
	if db == nil {
		return
	}

	migrator := db.Migrator()
	if migrator.HasTable("chat_messages") {
		return
	}

	if err := db.Exec(utils.CREATE_CHAT_MESSAGES_TABLE_SQL).Error; err != nil {
		log.Printf("auto create table chat_messages failed: %v", err)
		return
	}

	log.Printf("auto created table: chat_messages")
}

func buildMysqlDsn(c config.Config) string {
	mysqlConf := c.Database.Mysql
	if mysqlConf.Host == "" || mysqlConf.Port == "" || mysqlConf.Username == "" || mysqlConf.Dbname == "" {
		return ""
	}

	charset := mysqlConf.Charset
	if charset == "" {
		charset = "utf8mb4"
	}
	loc := mysqlConf.Loc
	if loc == "" {
		loc = "Local"
	}

	return fmt.Sprintf("%s:%s@tcp(%s:%s)/%s?charset=%s&parseTime=True&loc=%s",
		mysqlConf.Username,
		mysqlConf.Password,
		mysqlConf.Host,
		mysqlConf.Port,
		mysqlConf.Dbname,
		charset,
		loc,
	)
}

func initES(c config.Config) *elastic.Client {
	esConf := c.Database.ES
	if esConf.Host == "" || esConf.Port == 0 {
		return nil
	}

	esURL := fmt.Sprintf("http://%s:%d", esConf.Host, esConf.Port)
	opts := []elastic.ClientOptionFunc{
		elastic.SetURL(esURL),
		elastic.SetSniff(esConf.Sniff),
		elastic.SetMaxRetries(3),
		elastic.SetHealthcheckInterval(10 * time.Second),
		elastic.SetGzip(true),
	}
	if esConf.Username != "" {
		opts = append(opts, elastic.SetBasicAuth(esConf.Username, esConf.Password))
	}

	client, err := elastic.NewClient(opts...)
	if err != nil {
		panic(err)
	}
	return client
}

func initRabbitMQ(c config.Config) (*amqp.Connection, *amqp.Channel) {
	mqConf := c.MQ
	if mqConf.Host == "" || mqConf.Port == "" {
		return nil, nil
	}

	vhost := mqConf.Vhost
	if vhost == "" {
		vhost = "/"
	}
	url := fmt.Sprintf("amqp://%s:%s@%s:%s/%s", mqConf.Username, mqConf.Password, mqConf.Host, mqConf.Port, trimSlashPrefix(vhost))

	conn, err := amqp.Dial(url)
	if err != nil {
		panic(err)
	}

	channel, err := conn.Channel()
	if err != nil {
		panic(err)
	}

	queues := []string{"api-log-queue", "log-queue"}
	for _, queueName := range queues {
		_, err = channel.QueueDeclare(queueName, true, false, false, false, nil)
		if err != nil {
			panic(err)
		}
	}

	return conn, channel
}

func initMongoDB(c config.Config) *mongo.Client {
	mongoConf := c.Database.MongoDB
	if mongoConf.Host == "" || mongoConf.Port == "" {
		return nil
	}

	var mongoURI string
	if mongoConf.Username != "" && mongoConf.Password != "" {
		mongoURI = fmt.Sprintf("mongodb://%s:%s@%s:%s", mongoConf.Username, mongoConf.Password, mongoConf.Host, mongoConf.Port)
	} else {
		mongoURI = fmt.Sprintf("mongodb://%s:%s", mongoConf.Host, mongoConf.Port)
	}

	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	client, err := mongo.Connect(ctx, options.Client().ApplyURI(mongoURI))
	if err != nil {
		panic(err)
	}
	if err = client.Ping(ctx, nil); err != nil {
		panic(err)
	}

	return client
}

func initNacos(c config.Config) naming_client.INamingClient {
	nacosConf := c.Nacos
	if nacosConf.IpAddr == "" || nacosConf.Port == 0 {
		return nil
	}

	if nacosConf.CacheDir != "" {
		_ = os.MkdirAll(nacosConf.CacheDir, 0755)
	}
	if nacosConf.LogDir != "" {
		_ = os.MkdirAll(nacosConf.LogDir, 0755)
	}

	serverConfigs := []constant.ServerConfig{{
		IpAddr: nacosConf.IpAddr,
		Port:   uint64(nacosConf.Port),
	}}

	clientConfig := constant.ClientConfig{
		NamespaceId:         nacosConf.Namespace,
		TimeoutMs:           5000,
		NotLoadCacheAtStart: true,
		LogLevel:            "error",
		CacheDir:            nacosConf.CacheDir,
		LogDir:              nacosConf.LogDir,
	}

	namingClient, err := clients.NewNamingClient(vo.NacosClientParam{
		ClientConfig:  &clientConfig,
		ServerConfigs: serverConfigs,
	})
	if err != nil {
		panic(err)
	}

	if c.Host != "" && c.Port > 0 && nacosConf.ServiceName != "" {
		_, _ = namingClient.RegisterInstance(vo.RegisterInstanceParam{
			Ip:          c.Host,
			Port:        uint64(c.Port),
			ServiceName: nacosConf.ServiceName,
			GroupName:   nacosConf.GroupName,
			ClusterName: nacosConf.ClusterName,
			Weight:      1.0,
			Enable:      true,
			Healthy:     true,
			Ephemeral:   true,
		})
	}

	return namingClient
}

func trimSlashPrefix(v string) string {
	if len(v) > 0 && v[0] == '/' {
		return v[1:]
	}
	return v
}

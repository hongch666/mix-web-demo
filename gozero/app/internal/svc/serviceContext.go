// Code scaffolded by goctl. Safe to edit.
// goctl 1.9.2

package svc

import (
	"context"
	"fmt"
	"net"
	"os"
	"strings"
	"time"

	"app/common/hub"
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

	"github.com/nacos-group/nacos-sdk-go/v2/clients"
	"github.com/nacos-group/nacos-sdk-go/v2/clients/naming_client"
	"github.com/nacos-group/nacos-sdk-go/v2/common/constant"
	"github.com/nacos-group/nacos-sdk-go/v2/vo"
	"github.com/olivere/elastic/v7"
	amqp "github.com/rabbitmq/amqp091-go"
	"github.com/zeromicro/go-zero/core/logx"
	"github.com/zeromicro/go-zero/core/stores/sqlx"
	"github.com/zeromicro/go-zero/rest"
	"go.mongodb.org/mongo-driver/mongo"
	"go.mongodb.org/mongo-driver/mongo/options"
	"gorm.io/driver/mysql"
	"gorm.io/gorm"
)

var detectLocalIP = getLocalIPv4Address

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

	ChatHub *hub.ChatHub
	SSEHub  *hub.SSEHubManager

	Logger *logger.ZeroLogger

	UserContextMiddleware     rest.Middleware
	RecoveryMiddleware        rest.Middleware
	InternalServiceMiddleware rest.Middleware
}

func NewServiceContext(c config.Config) *ServiceContext {
	// 初始化日志
	zLogger, err := logger.NewZeroLogger(c.Logs.Path)
	if err != nil {
		logx.Errorf(utils.ZERO_LOGGER_INIT_FAIL, err)
		panic(err)
	}

	utils.InitInternalTokenUtil(c.InternalToken.Secret, c.InternalToken.Expiration)

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
		ChatHub:                &hub.ChatHub{ZeroLogger: zLogger},
		SSEHub: func() *hub.SSEHubManager {
			hub := hub.GetSSEHub()
			hub.ZeroLogger = zLogger
			return hub
		}(),
		Logger:                    zLogger,
		UserContextMiddleware:     middleware.NewUserContextMiddleware().Handle,
		RecoveryMiddleware:        middleware.NewRecoveryMiddleware(zLogger).Handle,
		InternalServiceMiddleware: middleware.NewInternalServiceMiddleware(zLogger).Handle,
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
		logx.Errorf(utils.GORM_INIT_FAIL, err)
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
		logx.Errorf(utils.AUTO_CREATE_TABLE_FAIL, err)
		return
	}

	logx.Info(utils.AUTO_CREATE_TABLE_SUCCESS)
}

func buildMysqlDsn(c config.Config) string {
	mysqlConf := c.Database.Mysql
	if mysqlConf.Host == "" || mysqlConf.Port == 0 || mysqlConf.Username == "" || mysqlConf.Dbname == "" {
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

	return fmt.Sprintf("%s:%s@tcp(%s:%d)/%s?charset=%s&parseTime=True&loc=%s",
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
		logx.Errorf(utils.ES_CLIENT_INIT_FAIL, err)
		panic(err)
	}
	return client
}

func initRabbitMQ(c config.Config) (*amqp.Connection, *amqp.Channel) {
	mqConf := c.MQ
	if mqConf.Host == "" || mqConf.Port == 0 {
		return nil, nil
	}

	vhost := mqConf.Vhost
	if vhost == "" {
		vhost = "/"
	}
	url := fmt.Sprintf("amqp://%s:%s@%s:%d/%s", mqConf.Username, mqConf.Password, mqConf.Host, mqConf.Port, trimSlashPrefix(vhost))

	conn, err := amqp.Dial(url)
	if err != nil {
		logx.Errorf(utils.RABBITMQ_CONNECTION_INIT_FAIL, err)
		panic(err)
	}

	channel, err := conn.Channel()
	if err != nil {
		logx.Errorf(utils.RABBITMQ_CHANNEL_INIT_FAIL, err)
		panic(err)
	}

	queues := []string{"api-log-queue", "article-log-queue"}
	for _, queueName := range queues {
		_, err = channel.QueueDeclare(queueName, true, false, false, false, nil)
		if err != nil {
			logx.Errorf(utils.RABBITMQ_DECLARE_QUEUE_FAIL, queueName, err)
			panic(err)
		}
	}

	return conn, channel
}

func initMongoDB(c config.Config) *mongo.Client {
	mongoConf := c.Database.MongoDB
	if mongoConf.Host == "" || mongoConf.Port == 0 {
		return nil
	}

	var mongoURI string
	if mongoConf.Username != "" && mongoConf.Password != "" {
		mongoURI = fmt.Sprintf("mongodb://%s:%s@%s:%d", mongoConf.Username, mongoConf.Password, mongoConf.Host, mongoConf.Port)
	} else {
		mongoURI = fmt.Sprintf("mongodb://%s:%d", mongoConf.Host, mongoConf.Port)
	}

	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	client, err := mongo.Connect(ctx, options.Client().ApplyURI(mongoURI))
	if err != nil {
		logx.Errorf(utils.MONGODB_CONNECTION_INIT_FAIL, err)
		panic(err)
	}
	if err = client.Ping(ctx, nil); err != nil {
		logx.Errorf(utils.MONGODB_PING_FAIL, err)
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
		_ = os.MkdirAll(nacosConf.CacheDir, 0o755)
	}
	if nacosConf.LogDir != "" {
		_ = os.MkdirAll(nacosConf.LogDir, 0o755)
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
		logx.Errorf(utils.NACOS_CLIENT_INIT_FAIL, err)
		panic(err)
	}

	registerIP := resolveNacosRegisterIP(c.Host)
	if strings.EqualFold(strings.TrimSpace(c.Mode), "dev") {
		registerIP = "127.0.0.1"
		logx.Info(utils.REGISTER_NACOS_DEV_MODE_MESSAGE)
	}

	if registerIP != "" && c.Port > 0 && nacosConf.ServiceName != "" {
		_, err = namingClient.RegisterInstance(vo.RegisterInstanceParam{
			Ip:          registerIP,
			Port:        uint64(c.Port),
			ServiceName: nacosConf.ServiceName,
			GroupName:   nacosConf.GroupName,
			ClusterName: nacosConf.ClusterName,
			Weight:      1.0,
			Enable:      true,
			Healthy:     true,
			Ephemeral:   true,
		})
		if err != nil {
			logx.Errorf(utils.NACOS_REGISTER_FAIL,
				nacosConf.ServiceName, registerIP, c.Port, nacosConf.GroupName, err)
			panic(err)
		}
	}

	return namingClient
}

func resolveNacosRegisterIP(listenHost string) string {
	listenHost = strings.TrimSpace(listenHost)
	if listenHost != "" && !isUnspecifiedHost(listenHost) {
		return listenHost
	}

	if localIP, err := detectLocalIP(); err == nil && localIP != "" {
		return localIP
	}

	return listenHost
}

func isUnspecifiedHost(host string) bool {
	switch strings.TrimSpace(host) {
	case "", "0.0.0.0", "::", "[::]":
		return true
	default:
		return false
	}
}

func getLocalIPv4Address() (string, error) {
	interfaces, err := net.Interfaces()
	if err != nil {
		return "", err
	}

	for _, iface := range interfaces {
		if iface.Flags&net.FlagUp == 0 || iface.Flags&net.FlagLoopback != 0 {
			continue
		}

		addrs, err := iface.Addrs()
		if err != nil {
			continue
		}

		for _, addr := range addrs {
			var ip net.IP
			switch v := addr.(type) {
			case *net.IPNet:
				ip = v.IP
			case *net.IPAddr:
				ip = v.IP
			}

			if ip == nil {
				continue
			}
			ip = ip.To4()
			if ip == nil {
				continue
			}
			if ip.IsLoopback() {
				continue
			}
			return ip.String(), nil
		}
	}

	return "", fmt.Errorf(utils.LOCAL_IPV4_ADDRESS_NOT_FOUND_ERROR)
}

func trimSlashPrefix(v string) string {
	if len(v) > 0 && v[0] == '/' {
		return v[1:]
	}
	return v
}

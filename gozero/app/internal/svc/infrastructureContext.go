package svc

import (
	"context"
	"fmt"
	"net"
	"os"
	"strconv"
	"strings"

	"app/common/constants"
	"app/common/utils"
	"app/internal/config"

	"github.com/nacos-group/nacos-sdk-go/v2/clients"
	"github.com/nacos-group/nacos-sdk-go/v2/clients/naming_client"
	"github.com/nacos-group/nacos-sdk-go/v2/common/constant"
	"github.com/nacos-group/nacos-sdk-go/v2/vo"
	"github.com/olivere/elastic/v7"
	"github.com/redis/go-redis/v9"
	rabbitmq "github.com/wagslane/go-rabbitmq"
	"github.com/zeromicro/go-zero/core/logx"
	"github.com/zeromicro/go-zero/core/stores/sqlx"
	"go.mongodb.org/mongo-driver/mongo"
	"go.mongodb.org/mongo-driver/mongo/options"
)

var detectLocalIP = getLocalIPv4Address

// 初始化基础设施上下文
func newInfrastructureContext(c config.Config, logger *utils.ZeroLogger) *InfrastructureContext {
	mysqlConn := initSqlx(c)
	initChatMessagesTable(logger, mysqlConn)

	return &InfrastructureContext{
		MySQLConn:         mysqlConn,
		ESClient:          initES(c, logger),
		RabbitMQPublisher: initRabbitMQ(c, logger),
		MongoClient:       initMongoDB(c, logger),
		RedisClient:       initRedis(c, logger),
		NamingClient:      initNacos(c, logger),
	}
}

// Close 关闭基础设施连接
func (ic *InfrastructureContext) Close() {
	if ic.RedisClient != nil {
		if err := ic.RedisClient.Close(); err != nil {
			logx.Errorf("关闭 Redis 连接失败: %v", err)
		}
	}

	if ic.MongoClient != nil {
		ctx, cancel := context.WithTimeout(context.Background(), constants.MongoDBDisconnectTimeout)
		defer cancel()
		if err := ic.MongoClient.Disconnect(ctx); err != nil {
			logx.Errorf("关闭 MongoDB 连接失败: %v", err)
		}
	}

	if ic.RabbitMQPublisher != nil {
		ic.RabbitMQPublisher.Close()
	}
}

// 初始化MySQL连接
func initSqlx(c config.Config) sqlx.SqlConn {
	dsn := buildMysqlDsn(c)
	if dsn == "" {
		return nil
	}

	sqlConf := c.Database.Mysql
	// 配置 SQL 日志：关闭普通日志时仅保留慢查询日志
	if !sqlConf.LogEnabled {
		sqlx.DisableStmtLog()
	}
	sqlx.SetSlowThreshold(sqlConf.GetSlowThreshold())

	return sqlx.NewMysql(dsn)
}

// 初始化需要的表结构
func initChatMessagesTable(logger *utils.ZeroLogger, conn sqlx.SqlConn) {
	if conn == nil {
		return
	}

	ctx, cancel := context.WithTimeout(context.Background(), constants.DDLOperationTimeout)
	defer cancel()

	if _, err := conn.ExecCtx(ctx, constants.CREATE_CHAT_MESSAGES_TABLE_SQL); err != nil {
		logger.Errorf(constants.ENSURE_CHAT_MESSAGES_TABLE_FAIL, err)
		return
	}

	logger.Info(constants.ENSURE_CHAT_MESSAGES_TABLE_SUCCESS)
}

// 构建 MySQL DSN
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

// 初始化 ElasticSearch 客户端
func initES(c config.Config, logger *utils.ZeroLogger) *elastic.Client {
	esConf := c.Database.ES
	if esConf.Host == "" || esConf.Port == 0 {
		return nil
	}

	esURL := fmt.Sprintf("http://%s:%d", esConf.Host, esConf.Port)
	opts := []elastic.ClientOptionFunc{
		elastic.SetURL(esURL),
		elastic.SetSniff(esConf.Sniff),
		elastic.SetMaxRetries(constants.ESMaxRetries),
		elastic.SetHealthcheckInterval(constants.ESHealthcheckInterval),
		elastic.SetGzip(true),
		elastic.SetHealthcheckTimeoutStartup(constants.ESHealthcheckTimeoutStartup),
		elastic.SetErrorLog(&esLoggerAdapter{}),
		elastic.SetInfoLog(&esLoggerAdapter{}),
	}
	if esConf.Username != "" {
		opts = append(opts, elastic.SetBasicAuth(esConf.Username, esConf.Password))
	}

	client, err := elastic.NewClient(opts...)
	if err != nil {
		logger.Errorf(constants.ES_CLIENT_INIT_FAIL, err)
		panic(err)
	}
	return client
}

// 初始化 RabbitMQ 发布者
func initRabbitMQ(c config.Config, logger *utils.ZeroLogger) *rabbitmq.Publisher {
	mqConf := c.MQ
	if mqConf.Host == "" || mqConf.Port == 0 {
		return nil
	}

	vhost := mqConf.Vhost
	if vhost == "" {
		vhost = "/"
	}
	url := fmt.Sprintf("amqp://%s:%s@%s:%d/%s",
		mqConf.Username,
		mqConf.Password,
		mqConf.Host,
		mqConf.Port,
		trimSlashPrefix(vhost),
	)

	conn, err := rabbitmq.NewConn(url)
	if err != nil {
		logger.Errorf(constants.RABBITMQ_CONNECTION_INIT_FAIL, err)
		panic(err)
	}

	publisher, err := rabbitmq.NewPublisher(conn, rabbitmq.WithPublisherOptionsLogging)
	if err != nil {
		logger.Errorf(constants.RABBITMQ_CONNECTION_INIT_FAIL, err)
		panic(err)
	}

	logger.Info(constants.RABBITMQ_CONNECT_SUCCESS)
	return publisher
}

// 初始化 MongoDB 客户端
func initMongoDB(c config.Config, logger *utils.ZeroLogger) *mongo.Client {
	mongoConf := c.Database.MongoDB
	if mongoConf.Host == "" || mongoConf.Port == 0 {
		return nil
	}

	var mongoURI string
	if mongoConf.Username != "" && mongoConf.Password != "" {
		mongoURI = fmt.Sprintf("mongodb://%s:%s@%s:%d",
			mongoConf.Username,
			mongoConf.Password,
			mongoConf.Host,
			mongoConf.Port,
		)
	} else {
		mongoURI = fmt.Sprintf("mongodb://%s:%d", mongoConf.Host, mongoConf.Port)
	}

	ctx, cancel := context.WithTimeout(context.Background(), constants.MongoDBConnectTimeout)
	defer cancel()

	client, err := mongo.Connect(ctx, options.Client().ApplyURI(mongoURI))
	if err != nil {
		logger.Errorf(constants.MONGODB_CONNECTION_INIT_FAIL, err)
		panic(err)
	}
	if err = client.Ping(ctx, nil); err != nil {
		logger.Errorf(constants.MONGODB_PING_FAIL, err)
		panic(err)
	}

	return client
}

// 初始化 Nacos 客户端
func initNacos(c config.Config, logger *utils.ZeroLogger) naming_client.INamingClient {
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
		TimeoutMs:           constants.NacosClientTimeoutMs,
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
		logger.Errorf(constants.NACOS_CLIENT_INIT_FAIL, err)
		panic(err)
	}

	registerIP := resolveNacosRegisterIP(c.Host)
	if strings.EqualFold(strings.TrimSpace(c.Mode), "dev") {
		registerIP = "127.0.0.1"
		logger.Info(constants.REGISTER_NACOS_DEV_MODE_MESSAGE)
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
			logger.Errorf(constants.NACOS_REGISTER_FAIL,
				nacosConf.ServiceName, registerIP, c.Port, nacosConf.GroupName, err)
			panic(err)
		}
	}

	return namingClient
}

// 初始化 Redis 客户端
func initRedis(c config.Config, logger *utils.ZeroLogger) *redis.Client {
	redisConf := c.Database.Redis
	if redisConf.Host == "" || redisConf.Port == 0 {
		return nil
	}

	db, _ := strconv.Atoi(redisConf.DB)
	client := redis.NewClient(&redis.Options{
		Addr:     fmt.Sprintf("%s:%d", redisConf.Host, redisConf.Port),
		Username: redisConf.Username,
		Password: redisConf.Password,
		DB:       db,
	})

	ctx, cancel := context.WithTimeout(context.Background(), constants.RedisConnectTimeout)
	defer cancel()
	if err := client.Ping(ctx).Err(); err != nil {
		logger.Errorf(constants.REDIS_INIT_FAIL, err)
		panic(err)
	}

	logger.Infof(constants.REDIS_CONNECT_SUCCESS, redisConf.Host, redisConf.Port, db)
	return client
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
			switch value := addr.(type) {
			case *net.IPNet:
				ip = value.IP
			case *net.IPAddr:
				ip = value.IP
			}
			if ip == nil {
				continue
			}
			ip = ip.To4()
			if ip == nil || ip.IsLoopback() {
				continue
			}
			return ip.String(), nil
		}
	}

	return "", fmt.Errorf(constants.LOCAL_IPV4_ADDRESS_NOT_FOUND_ERROR)
}

func trimSlashPrefix(value string) string {
	if len(value) > 0 && value[0] == '/' {
		return value[1:]
	}
	return value
}

type esLoggerAdapter struct{}

func (l *esLoggerAdapter) Printf(format string, v ...interface{}) {
	logx.Infof(format, v...)
}

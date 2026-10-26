package svc

import (
	"context"
	"database/sql"
	"fmt"
	"net"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"time"

	"app/common/constants"
	"app/common/utils"
	"app/internal/config"

	_ "github.com/go-sql-driver/mysql"
	"github.com/nacos-group/nacos-sdk-go/v2/clients"
	"github.com/nacos-group/nacos-sdk-go/v2/clients/naming_client"
	"github.com/nacos-group/nacos-sdk-go/v2/common/constant"
	"github.com/nacos-group/nacos-sdk-go/v2/vo"
	"github.com/olivere/elastic/v7"
	"github.com/redis/go-redis/v9"
	rabbitmq "github.com/wagslane/go-rabbitmq"
	"github.com/zeromicro/go-zero/core/logx"
	"github.com/zeromicro/go-zero/core/stores/sqlx"
)

var detectLocalIP = getLocalIPv4Address

// sleepBeforeNacosRetry 注册重试前的等待函数，测试可替换为不回真实等待的实现
var sleepBeforeNacosRetry = time.Sleep

// nacosBackgroundRunner 后台补注册的启动函数，测试可替换为同步执行以避免并发
var nacosBackgroundRunner = func(logger *utils.ZeroLogger, taskName string, task func()) {
	utils.SafeGo(logger, taskName, task)
}

// 初始化基础设施上下文
func newInfrastructureContext(c config.Config, logger *utils.ZeroLogger) *InfrastructureContext {
	mysqlConn := initSqlx(c, logger)
	initChatMessagesTable(logger, mysqlConn)

	return &InfrastructureContext{
		MySQLConn:         mysqlConn,
		RawMySQL:          initRawMysql(c, logger),
		ESClient:          initES(c, logger),
		RabbitMQPublisher: initRabbitMQ(c, logger),
		RedisClient:       initRedis(c, logger),
		NamingClient:      initNacos(c, logger),
	}
}

// initRawMysql 初始化标准库 MySQL 连接（供 SQL 工具等动态列查询手动扫描结果）
func initRawMysql(c config.Config, logger *utils.ZeroLogger) *sql.DB {
	dsn := buildMysqlDsn(c)
	if dsn == "" {
		logger.Warning(constants.RAW_MYSQL_CONFIG_MISSING_DEGRADE)
		return nil
	}
	rawDB, err := sql.Open(constants.SQL_TOOLS_MYSQL_DRIVER, dsn)
	if err != nil {
		logger.Error(constants.SQL_TOOLS_QUERY_FAILED + ": " + err.Error())
		return nil
	}
	rawDB.SetMaxOpenConns(10)
	rawDB.SetMaxIdleConns(5)
	return rawDB
}

// Close 关闭基础设施连接
func (ic *InfrastructureContext) Close() {
	if ic.RawMySQL != nil {
		if err := ic.RawMySQL.Close(); err != nil {
			logx.Errorf(constants.MYSQL_CLOSE_FAIL, err)
		}
	}

	if ic.RedisClient != nil {
		if err := ic.RedisClient.Close(); err != nil {
			logx.Errorf(constants.REDIS_CLOSE_FAIL, err)
		}
	}

	if ic.RabbitMQPublisher != nil {
		ic.RabbitMQPublisher.Close()
	}
}

// 初始化MySQL连接
func initSqlx(c config.Config, logger *utils.ZeroLogger) sqlx.SqlConn {
	dsn := buildMysqlDsn(c)
	if dsn == "" {
		logger.Warning(constants.MYSQL_CONFIG_MISSING_DEGRADE)
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
		logger.Warning(constants.ES_CONFIG_MISSING_DEGRADE)
		return nil
	}

	esURL := fmt.Sprintf("http://%s:%d", esConf.Host, esConf.Port)
	esLogger := &esLoggerAdapter{logger: logger}
	opts := []elastic.ClientOptionFunc{
		elastic.SetURL(esURL),
		elastic.SetSniff(esConf.Sniff),
		// SetMaxRetries 在 olivere/elastic v7 中标记废弃，但当前仍依赖其重试语义，替换为自定义 Retry 实现会影响 ES 寻址行为，这里显式保留并忽略废弃告警
		//nolint:staticcheck // SA1019: 保留 olivere/elastic 内置重试策略
		elastic.SetMaxRetries(constants.ESMaxRetries),
		elastic.SetHealthcheckInterval(constants.ESHealthcheckInterval),
		elastic.SetGzip(true),
		elastic.SetHealthcheckTimeoutStartup(constants.ESHealthcheckTimeoutStartup),
		elastic.SetErrorLog(esLogger),
		elastic.SetInfoLog(esLogger),
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
		logger.Warning(constants.RABBITMQ_CONFIG_MISSING_DEGRADE)
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

// 初始化 Nacos 客户端并注册当前实例
func initNacos(c config.Config, logger *utils.ZeroLogger) naming_client.INamingClient {
	nacosConf := c.Nacos
	if nacosConf.IpAddr == "" || nacosConf.Port == 0 {
		logger.Warning(constants.NACOS_CONFIG_MISSING_DEGRADE)
		return nil
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
		CacheDir:            resolveNacosWritableDir(constants.NacosCacheDirName, nacosConf.CacheDir, logger),
		LogDir:              resolveNacosWritableDir(constants.NacosLogDirName, nacosConf.LogDir, logger),
	}

	namingClient, err := clients.NewNamingClient(vo.NacosClientParam{
		ClientConfig:  &clientConfig,
		ServerConfigs: serverConfigs,
	})
	if err != nil {
		logger.Errorf(constants.NACOS_CLIENT_INIT_FAIL, err)
		panic(err)
	}

	registerNacosInstance(namingClient, c, logger)
	return namingClient
}

// nacosInstanceRegistrar 抽象 Nacos 实例注册能力，便于测试注册重试与降级分支
type nacosInstanceRegistrar interface {
	RegisterInstance(param vo.RegisterInstanceParam) (bool, error)
}

// registerNacosInstance 注册当前实例到 Nacos，失败按固定间隔重试，重试耗尽只告警降级，不阻断服务启动
func registerNacosInstance(client nacosInstanceRegistrar, c config.Config, logger *utils.ZeroLogger) {
	nacosConf := c.Nacos
	if client == nil || nacosConf.ServiceName == "" || c.Port <= 0 {
		return
	}

	// 网关以容器运行，注册地址必须是容器能回连的地址，固定 127.0.0.1 会让网关连到容器自身，显式配置 SERVER_IP 时以它为准，未指定（空、0.0.0.0）则自动探测本机 IP
	registerIP := resolveNacosRegisterIP(c.Host)
	if registerIP == "" {
		logger.Warning(constants.NACOS_REGISTER_IP_MISSING_DEGRADE)
		return
	}

	param := vo.RegisterInstanceParam{
		Ip:          registerIP,
		Port:        uint64(c.Port),
		ServiceName: nacosConf.ServiceName,
		GroupName:   nacosConf.GroupName,
		ClusterName: nacosConf.ClusterName,
		Weight:      1.0,
		Enable:      true,
		Healthy:     true,
		Ephemeral:   true,
	}

	registered, lastErr := tryRegisterNacosInstance(client, param, constants.NacosRegisterRetries, logger)
	if registered {
		return
	}

	logger.Errorf(constants.NACOS_REGISTER_FAIL,
		nacosConf.ServiceName, registerIP, c.Port, nacosConf.GroupName, lastErr)
	logger.Warning(constants.NACOS_REGISTER_DEGRADE_WARNING)

	// Nacos 启动慢于本服务时，启动阶段的重试可能全部落空，转入后台继续补注册，避免实例永久不被网关发现
	nacosBackgroundRunner(logger, constants.NacosRegisterTaskName, func() {
		if retried, _ := tryRegisterNacosInstance(client, param, constants.NacosRegisterBackgroundRetries, logger); !retried {
			logger.Errorf(constants.NACOS_REGISTER_BACKGROUND_GIVE_UP_ERROR,
				nacosConf.ServiceName, registerIP, c.Port)
		}
	})
}

// tryRegisterNacosInstance 按固定间隔尝试注册，成功返回 true，重试耗尽返回 false 与最后一次错误
func tryRegisterNacosInstance(
	client nacosInstanceRegistrar,
	param vo.RegisterInstanceParam,
	attempts int,
	logger *utils.ZeroLogger,
) (bool, error) {
	var lastErr error
	for attempt := 1; attempt <= attempts; attempt++ {
		_, err := client.RegisterInstance(param)
		if err == nil {
			logger.Infof(constants.NACOS_REGISTERED_MESSAGE, param.Ip, param.Port)
			return true, nil
		}
		lastErr = err
		logger.Warningf(constants.NACOS_REGISTER_RETRY_WARNING, attempt, attempts, err)
		if attempt < attempts {
			sleepBeforeNacosRetry(constants.NacosRegisterRetryInterval)
		}
	}

	return false, lastErr
}

// resolveNacosWritableDir 返回可写的 Nacos SDK 目录，配置目录不可写时回退系统临时目录，避免容器内非 root 用户写 SDK 日志失败
func resolveNacosWritableDir(kind string, configuredPath string, logger *utils.ZeroLogger) string {
	fallbackPath := filepath.Join(os.TempDir(), constants.NacosTempDirName, kind)
	candidates := []string{fallbackPath}
	if configuredPath != "" {
		candidates = []string{configuredPath, fallbackPath}
	}

	var lastErr error
	for _, candidate := range candidates {
		if err := ensureWritableDir(candidate); err != nil {
			lastErr = err
			logger.Warningf(constants.NACOS_DIR_UNUSABLE_WARNING, candidate, err)
			continue
		}
		if configuredPath != "" && candidate != configuredPath {
			logger.Warningf(constants.NACOS_DIR_FALLBACK_WARNING, configuredPath, candidate)
		}
		return candidate
	}

	logger.Errorf(constants.NACOS_DIR_UNAVAILABLE_ERROR, kind, lastErr)
	return fallbackPath
}

// ensureWritableDir 创建目录并写入探针文件确认可写，MkdirAll 成功不代表当前用户对目录有写权限
func ensureWritableDir(dir string) error {
	if err := os.MkdirAll(dir, 0o755); err != nil {
		return err
	}

	probe, err := os.CreateTemp(dir, ".write-probe-")
	if err != nil {
		return err
	}
	probePath := probe.Name()
	if err := probe.Close(); err != nil {
		return err
	}

	return os.Remove(probePath)
}

// 初始化 Redis 客户端
func initRedis(c config.Config, logger *utils.ZeroLogger) *redis.Client {
	redisConf := c.Database.Redis
	if redisConf.Host == "" || redisConf.Port == 0 {
		logger.Warning(constants.REDIS_CONFIG_MISSING_DEGRADE)
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

// resolveNacosRegisterIP 确定 Nacos 注册 IP，优先取配置的监听地址，未指定或全零地址时自动探测本机 IP
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

// isUnspecifiedHost 判断主机地址是否为空串或 0.0.0.0、:: 等未指定地址
func isUnspecifiedHost(host string) bool {
	switch strings.TrimSpace(host) {
	case "", "0.0.0.0", "::", "[::]":
		return true
	default:
		return false
	}
}

// getLocalIPv4Address 遍历网卡获取首个已启用且非回环的 IPv4 地址
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

// trimSlashPrefix 去除字符串开头的斜杠，用于拼接 RabbitMQ 连接地址中的 vhost
func trimSlashPrefix(value string) string {
	if len(value) > 0 && value[0] == '/' {
		return value[1:]
	}
	return value
}

// 将 ES 客户端运行期日志适配转发到 ZeroLogger 输出
type esLoggerAdapter struct {
	logger *utils.ZeroLogger
}

// Printf 将 ES 客户端运行期日志路由到 ZeroLogger，未持有时退化为 logx
func (l *esLoggerAdapter) Printf(format string, v ...interface{}) {
	if l != nil && l.logger != nil {
		l.logger.Infof(format, v...)
		return
	}
	logx.Infof(format, v...)
}

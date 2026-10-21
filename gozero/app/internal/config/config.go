// Code scaffolded by goctl. Safe to edit.

package config

import (
	"time"

	"github.com/zeromicro/go-zero/rest"
)

// 服务总配置，聚合 REST、任务调度、Nacos、存储、消息队列、日志与远程调用配置
type Config struct {
	rest.RestConf
	Prefix        string              `json:"prefix"`
	Task          TaskConfig          `json:"task"`
	Nacos         NacosConfig         `json:"nacos"`
	Database      DatabaseConfig      `json:"database"`
	MQ            MQConfig            `json:"mq"`
	Logs          LogsConfig          `json:"logs"`
	InternalToken InternalTokenConfig `json:"internal-token"`
	RemoteCall    RemoteCallConfig    `json:"remote-call"`
}

// TaskConfig 定时任务调度配置
type TaskConfig struct {
	// Enabled 为 false 时不注册本地 cron 任务，改由外部调度器（DolphinScheduler）触发 /task/* 接口
	Enabled bool `json:"enabled"`
}

// Nacos 注册中心连接参数与命名空间配置
type NacosConfig struct {
	IpAddr      string `json:"ipAddr"`
	Port        int    `json:"port"`
	Namespace   string `json:"namespace"`
	ServiceName string `json:"serviceName"`
	GroupName   string `json:"groupName"`
	ClusterName string `json:"clusterName"`
	CacheDir    string `json:"cacheDir"`
	LogDir      string `json:"logDir"`
}

// MySQL 连接参数与 SQL 日志开关、慢查询阈值配置
type MysqlConfig struct {
	Host          string `json:"host"`
	Port          int    `json:"port"`
	Username      string `json:"username"`
	Password      string `json:"password"`
	Dbname        string `json:"dbname"`
	Charset       string `json:"charset"`
	Loc           string `json:"loc"`
	LogEnabled    bool   `json:"sqlLogEnabled"` // SQL 普通日志开关，默认 true
	SlowThreshold int    `json:"slowThreshold"` // 慢查询阈值(毫秒)，默认 500
}

// GetSlowThreshold 获取慢查询阈值，返回 time.Duration，默认 500ms
func (m MysqlConfig) GetSlowThreshold() time.Duration {
	if m.SlowThreshold <= 0 {
		return 500 * time.Millisecond
	}
	return time.Duration(m.SlowThreshold) * time.Millisecond
}

// Elasticsearch 连接参数与查询 DSL 日志开关配置
type ESConfig struct {
	Host     string `json:"host"`
	Port     int    `json:"port"`
	Username string `json:"username"`
	Password string `json:"password"`
	Sniff    bool   `json:"sniff"`
	// DSLLogEnabled 查询 DSL 日志开关，默认关闭；开启后每次搜索输出一份等价请求体
	DSLLogEnabled bool `json:"dslLogEnabled"`
}

// 存储层配置集合，聚合 MySQL、ES 与 Redis
type DatabaseConfig struct {
	Mysql MysqlConfig `json:"mysql"`
	ES    ESConfig    `json:"es"`
	Redis RedisConfig `json:"redis"`
}

// Redis 连接参数配置
type RedisConfig struct {
	Host     string `json:"host"`
	Port     int    `json:"port"`
	Username string `json:"username"`
	Password string `json:"password"`
	DB       string `json:"db"`
}

// RabbitMQ 连接参数配置
type MQConfig struct {
	Username string `json:"username"`
	Password string `json:"password"`
	Host     string `json:"host"`
	Port     int    `json:"port"`
	Vhost    string `json:"vhost"`
}

// 内部服务调用令牌的密钥与过期时间配置
type InternalTokenConfig struct {
	Secret     string `json:"secret"`
	Expiration int64  `json:"expiration"`
}

// 日志文件输出路径配置
type LogsConfig struct {
	Path string `json:"path"`
}

// 远程服务调用的超时、重试与退避策略配置
type RemoteCallConfig struct {
	Timeout        int                  `json:"timeout"`        // 请求超时时间（毫秒）
	MaxRetries     int                  `json:"maxRetries"`     // 最大重试次数
	InitialBackoff int                  `json:"initialBackoff"` // 初始退避时间（毫秒）
	MaxBackoff     int                  `json:"maxBackoff"`     // 最大退避时间（毫秒）
	CircuitBreaker CircuitBreakerConfig `json:"circuitBreaker"` // 熔断器配置
}

// 熔断器的失败阈值与恢复超时配置
type CircuitBreakerConfig struct {
	FailureThreshold int `json:"failureThreshold"` // 失败阈值
	RecoveryTimeout  int `json:"recoveryTimeout"`  // 恢复超时时间（毫秒）
}

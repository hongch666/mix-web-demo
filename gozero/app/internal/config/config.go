// Code scaffolded by goctl. Safe to edit.
// goctl 1.9.2

package config

import (
	"time"

	"github.com/zeromicro/go-zero/rest"
)

type Config struct {
	rest.RestConf
	Prefix        string              `json:"prefix"`
	Nacos         NacosConfig         `json:"nacos"`
	Database      DatabaseConfig      `json:"database"`
	MQ            MQConfig            `json:"mq"`
	Logs          LogsConfig          `json:"logs"`
	InternalToken InternalTokenConfig `json:"internal-token"`
	RemoteCall    RemoteCallConfig    `json:"remote-call"`
	Grpc          GrpcConfig          `json:"grpc"`
}

type GrpcConfig struct {
	Enabled bool `json:"enabled"`
	Port    int  `json:"port"`
}

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

type ESConfig struct {
	Host     string `json:"host"`
	Port     int    `json:"port"`
	Username string `json:"username"`
	Password string `json:"password"`
	Sniff    bool   `json:"sniff"`
}

type DatabaseConfig struct {
	Mysql MysqlConfig `json:"mysql"`
	ES    ESConfig    `json:"es"`
	Redis RedisConfig `json:"redis"`
}

type RedisConfig struct {
	Host     string `json:"host"`
	Port     int    `json:"port"`
	Username string `json:"username"`
	Password string `json:"password"`
	DB       string `json:"db"`
}

type MQConfig struct {
	Username string `json:"username"`
	Password string `json:"password"`
	Host     string `json:"host"`
	Port     int    `json:"port"`
	Vhost    string `json:"vhost"`
}

type InternalTokenConfig struct {
	Secret     string `json:"secret"`
	Expiration int64  `json:"expiration"`
}

type LogsConfig struct {
	Path string `json:"path"`
}

type RemoteCallConfig struct {
	Timeout        int                  `json:"timeout"`        // 请求超时时间（毫秒）
	MaxRetries     int                  `json:"maxRetries"`     // 最大重试次数
	InitialBackoff int                  `json:"initialBackoff"` // 初始退避时间（毫秒）
	MaxBackoff     int                  `json:"maxBackoff"`     // 最大退避时间（毫秒）
	CircuitBreaker CircuitBreakerConfig `json:"circuitBreaker"` // 熔断器配置
	Protocol       string               `json:"protocol"`       // grpc-first 或 http-only
}

type CircuitBreakerConfig struct {
	FailureThreshold int `json:"failureThreshold"` // 失败阈值
	RecoveryTimeout  int `json:"recoveryTimeout"`  // 恢复超时时间（毫秒）
}

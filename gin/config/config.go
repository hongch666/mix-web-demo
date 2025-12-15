package config

import (
	"fmt"

	"github.com/spf13/viper"
)

type ServerConfig struct {
	Ip   string `mapstructure:"ip"`
	Port int    `mapstructure:"port"`
}

type NacosConfig struct {
	IpAddr      string `mapstructure:"ipAddr"`
	Port        int    `mapstructure:"port"`
	Namespace   string `mapstructure:"namespace"`
	ServiceName string `mapstructure:"serviceName"`
	GroupName   string `mapstructure:"groupName"`
	ClusterName string `mapstructure:"clusterName"`
	CacheDir    string `mapstructure:"cacheDir"`
	LogDir      string `mapstructure:"logDir"`
}

type MysqlConfig struct {
	Host     string `mapstructure:"host"`
	Port     string `mapstructure:"port"`
	Username string `mapstructure:"username"`
	Password string `mapstructure:"password"`
	Dbname   string `mapstructure:"dbname"`
	Charset  string `mapstructure:"charset"`
	Loc      string `mapstructure:"loc"`
}

type ESConfig struct {
	Host     string `mapstructure:"host"`
	Port     int    `mapstructure:"port"`
	Username string `mapstructure:"username"`
	Password string `mapstructure:"password"`
	Sniff    bool   `mapstructure:"sniff"`
}

type MongoDBConfig struct {
	Host     string `mapstructure:"host"`
	Port     string `mapstructure:"port"`
	Username string `mapstructure:"username"`
	Password string `mapstructure:"password"`
	Database string `mapstructure:"database"`
}

type DatabaseConfig struct {
	Mysql   MysqlConfig   `mapstructure:"mysql"`
	ES      ESConfig      `mapstructure:"es"`
	MongoDB MongoDBConfig `mapstructure:"mongodb"`
}

type MQConfig struct {
	Username string `mapstructure:"username"`
	Password string `mapstructure:"password"`
	Host     string `mapstructure:"host"`
	Port     string `mapstructure:"port"`
	Vhost    string `mapstructure:"vhost"`
}

type AppConfig struct {
	Server   ServerConfig   `mapstructure:"server"`
	Nacos    NacosConfig    `mapstructure:"nacos"`
	Database DatabaseConfig `mapstructure:"database"`
	MQ       MQConfig       `mapstructure:"mq"`
	Logs     LogsConfig     `mapstructure:"logs"`
	Search   SearchConfig   `mapstructure:"search"`
}

type LogsConfig struct {
	Path string `mapstructure:"path"`
}

type SearchConfig struct {
	ESScoreWeight      float64 `mapstructure:"es_score_weight"`
	AIRatingWeight     float64 `mapstructure:"ai_rating_weight"`
	UserRatingWeight   float64 `mapstructure:"user_rating_weight"`
	ViewsWeight        float64 `mapstructure:"views_weight"`
	MaxViewsNormalized float64 `mapstructure:"max_views_normalized"`
}

var Config AppConfig

func InitConfig() {
	viper.SetConfigName("application") // 文件名 (不包含扩展名)
	viper.SetConfigType("yaml")        // 文件类型
	viper.AddConfigPath(".")           // 查找路径

	err := viper.ReadInConfig()
	if err != nil {
		panic(fmt.Errorf("配置文件读取失败: %s", err))
	}

	err = viper.Unmarshal(&Config)
	if err != nil {
		panic(fmt.Errorf("配置映射失败: %s", err))
	}
}

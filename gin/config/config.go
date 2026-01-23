package config

import (
	"gin_proj/common/exceptions"
	"os"
	"regexp"
	"strings"

	"github.com/joho/godotenv"
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
	ESScoreWeight         float64 `mapstructure:"es_score_weight"`
	AIRatingWeight        float64 `mapstructure:"ai_rating_weight"`
	UserRatingWeight      float64 `mapstructure:"user_rating_weight"`
	ViewsWeight           float64 `mapstructure:"views_weight"`
	LikesWeight           float64 `mapstructure:"likes_weight"`
	CollectsWeight        float64 `mapstructure:"collects_weight"`
	AuthorFollowWeight    float64 `mapstructure:"author_follow_weight"`
	RecencyWeight         float64 `mapstructure:"recency_weight"`
	MaxViewsNormalized    float64 `mapstructure:"max_views_normalized"`
	MaxLikesNormalized    float64 `mapstructure:"max_likes_normalized"`
	MaxCollectsNormalized float64 `mapstructure:"max_collects_normalized"`
	MaxFollowsNormalized  float64 `mapstructure:"max_follows_normalized"`
	RecencyDecayDays      int64   `mapstructure:"recency_decay_days"`
}

var Config AppConfig

// resolveEnvVars 递归替换YAML中的环境变量占位符
func resolveEnvVars(data []byte) []byte {
	// 匹配 ${VAR_NAME:default_value} 或 ${VAR_NAME}
	pattern := regexp.MustCompile(`\$\{([^:}]+)(?::([^}]*))?\}`)
	result := pattern.ReplaceAllStringFunc(string(data), func(match string) string {
		// 解析占位符
		parts := pattern.FindStringSubmatch(match)
		if len(parts) < 2 {
			return match
		}
		varName := parts[1]
		defaultVal := ""
		if len(parts) > 2 && parts[2] != "" {
			defaultVal = parts[2]
		}

		// 获取环境变量，如果不存在则使用默认值
		value := os.Getenv(varName)
		if value == "" {
			value = defaultVal
		}
		return value
	})
	return []byte(result)
}

func InitConfig() {
	// 加载 .env 文件
	_ = godotenv.Load(".env")

	viper.SetConfigName("application") // 文件名 (不包含扩展名)
	viper.SetConfigType("yaml")        // 文件类型
	viper.AddConfigPath(".")           // 查找路径

	// 读取原始文件内容，替换占位符
	configFile, err := os.ReadFile("application.yaml")
	if err != nil {
		panic(exceptions.NewBusinessError(READ_CONFIG_FILE_ERROR_MESSAGE, err.Error()))
	}

	// 替换环境变量
	configFile = resolveEnvVars(configFile)

	// 用处理后的内容配置 viper
	viper.SetConfigType("yaml")
	err = viper.ReadConfig(strings.NewReader(string(configFile)))
	if err != nil {
		panic(exceptions.NewBusinessError(PARSE_CONFIG_FILE_ERROR_MESSAGE, err.Error()))
	}

	err = viper.Unmarshal(&Config)
	if err != nil {
		panic(exceptions.NewBusinessError(CONFIG_MAPPING_ERROR_MESSAGE, err.Error()))
	}
}

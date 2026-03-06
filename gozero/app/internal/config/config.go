// Code scaffolded by goctl. Safe to edit.
// goctl 1.9.2

package config

import "github.com/zeromicro/go-zero/rest"

type Config struct {
	rest.RestConf

	Prefix string `json:"prefix"`

	Nacos NacosConfig `json:"nacos"`

	Database DatabaseConfig `json:"database"`
	MQ       MQConfig       `json:"mq"`

	Logs   LogsConfig   `json:"logs"`
	Search SearchConfig `json:"search"`

	InternalToken InternalTokenConfig `json:"internal-token"`
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
	Host     string `json:"host"`
	Port     int    `json:"port"`
	Username string `json:"username"`
	Password string `json:"password"`
	Dbname   string `json:"dbname"`
	Charset  string `json:"charset"`
	Loc      string `json:"loc"`
}

type ESConfig struct {
	Host     string `json:"host"`
	Port     int    `json:"port"`
	Username string `json:"username"`
	Password string `json:"password"`
	Sniff    bool   `json:"sniff"`
}

type MongoDBConfig struct {
	Host     string `json:"host"`
	Port     int    `json:"port"`
	Username string `json:"username"`
	Password string `json:"password"`
	Database string `json:"database"`
}

type DatabaseConfig struct {
	Mysql   MysqlConfig   `json:"mysql"`
	ES      ESConfig      `json:"es"`
	MongoDB MongoDBConfig `json:"mongodb"`
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

type SearchConfig struct {
	ESScoreWeight         float64 `json:"es_score_weight"`
	AIRatingWeight        float64 `json:"ai_rating_weight"`
	UserRatingWeight      float64 `json:"user_rating_weight"`
	ViewsWeight           float64 `json:"views_weight"`
	LikesWeight           float64 `json:"likes_weight"`
	CollectsWeight        float64 `json:"collects_weight"`
	AuthorFollowWeight    float64 `json:"author_follow_weight"`
	RecencyWeight         float64 `json:"recency_weight"`
	MaxViewsNormalized    float64 `json:"max_views_normalized"`
	MaxLikesNormalized    float64 `json:"max_likes_normalized"`
	MaxCollectsNormalized float64 `json:"max_collects_normalized"`
	MaxFollowsNormalized  float64 `json:"max_follows_normalized"`
	RecencyDecayDays      int64   `json:"recency_decay_days"`
}

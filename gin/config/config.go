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
	Url   string `mapstructure:"url"`
	Sniff bool   `mapstructure:"sniff"`
}

type DatabaseConfig struct {
	Mysql MysqlConfig `mapstructure:"mysql"`
	ES    ESConfig    `mapstructure:"es"`
}

type AppConfig struct {
	Server   ServerConfig   `mapstructure:"server"`
	Nacos    NacosConfig    `mapstructure:"nacos"`
	Database DatabaseConfig `mapstructure:"database"`
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

package config

import (
	"log"

	"github.com/olivere/elastic/v7"
)

var (
	ESClient *elastic.Client
)

func InitES() {
	var err error

	// 构建连接选项
	opts := []elastic.ClientOptionFunc{
		elastic.SetURL(Config.Database.ES.Url),
		elastic.SetSniff(Config.Database.ES.Sniff),
	}

	// 如果有用户名才添加
	if Config.Database.ES.Username != "" {
		opts = append(opts, elastic.SetBasicAuth(Config.Database.ES.Username, Config.Database.ES.Password))
		log.Printf("ES连接使用用户名认证: %s", Config.Database.ES.Username)
	}

	ESClient, err = elastic.NewClient(opts...)

	if err != nil {
		log.Fatalf("ES连接失败: %v", err)
	}

	log.Println("ES连接成功")
}

package config

import (
	"fmt"
	"log"

	"github.com/olivere/elastic/v7"
)

var (
	ESClient *elastic.Client
)

func InitES() {
	var err error

	// 构建 Elasticsearch URL
	host := Config.Database.ES.Host
	port := Config.Database.ES.Port
	esUrl := fmt.Sprintf("http://%s:%d", host, port)

	// 构建连接选项
	opts := []elastic.ClientOptionFunc{
		elastic.SetURL(esUrl),
		elastic.SetSniff(Config.Database.ES.Sniff),
	}

	// 如果有用户名才添加认证
	if Config.Database.ES.Username != "" {
		opts = append(opts, elastic.SetBasicAuth(Config.Database.ES.Username, Config.Database.ES.Password))
		log.Printf("ES连接使用用户名认证: %s", Config.Database.ES.Username)
	}

	ESClient, err = elastic.NewClient(opts...)

	if err != nil {
		log.Fatalf("ES连接失败: %v", err)
	}

	log.Printf("ES连接成功: %s", esUrl)
}

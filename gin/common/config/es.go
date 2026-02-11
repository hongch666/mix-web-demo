package config

import (
	"fmt"
	"log"
	"time"

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
		// 优化连接池配置，防止资源耗尽
		elastic.SetMaxRetries(3),                         // 最多重试3次
		elastic.SetHealthcheckInterval(10 * time.Second), // 健康检查间隔
		elastic.SetGzip(true),                            // 启用gzip压缩减少网络传输
	}

	// 如果有用户名才添加认证
	if Config.Database.ES.Username != "" {
		opts = append(opts, elastic.SetBasicAuth(Config.Database.ES.Username, Config.Database.ES.Password))
		log.Printf(ES_CONNECTION_WITH_AUTH_MESSAGE, Config.Database.ES.Username)
	}

	ESClient, err = elastic.NewClient(opts...)

	if err != nil {
		log.Fatalf(ES_CONNECTION_FAILURE_MESSAGE, err)
	}

	log.Printf(ES_CONNECTION_SUCCESS_MESSAGE, esUrl)
}

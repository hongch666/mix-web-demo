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
	ESClient, err = elastic.NewClient(
		elastic.SetURL("http://127.0.0.1:9200"),
		elastic.SetSniff(false),
	)

	if err != nil {
		log.Fatalf("ES连接失败: %v", err)
	}

	log.Println("ES连接成功")
}

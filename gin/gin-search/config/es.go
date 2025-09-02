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
		elastic.SetURL(Config.Database.ES.Url),
		elastic.SetSniff(Config.Database.ES.Sniff),
	)

	if err != nil {
		log.Fatalf("ES连接失败: %v", err)
	}

	log.Println("ES连接成功")
}

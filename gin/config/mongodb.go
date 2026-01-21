package config

import (
	"context"
	"fmt"
	"gin_proj/common/exceptions"
	"log"
	"time"

	"go.mongodb.org/mongo-driver/mongo"
	"go.mongodb.org/mongo-driver/mongo/options"
)

var MongoClient *mongo.Client

func InitMongoDB() {
	// 根据 host、port、username、password 构建 URI
	host := Config.Database.MongoDB.Host
	port := Config.Database.MongoDB.Port
	username := Config.Database.MongoDB.Username
	password := Config.Database.MongoDB.Password

	var mongoURI string
	// 如果有用户名和密码，构建认证 URI
	if username != "" && password != "" {
		mongoURI = fmt.Sprintf("mongodb://%s:%s@%s:%s", username, password, host, port)
		log.Printf("MongoDB 使用认证连接: %s:%s@%s:%s", username, "***", host, port)
	} else {
		mongoURI = fmt.Sprintf("mongodb://%s:%s", host, port)
		log.Printf("MongoDB 连接 (无认证): %s:%s", host, port)
	}

	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	clientOptions := options.Client().ApplyURI(mongoURI)
	client, err := mongo.Connect(ctx, clientOptions)
	if err != nil {
		panic(exceptions.NewBusinessError("MongoDB 连接失败", err.Error()))
	}

	// 验证连接
	err = client.Ping(ctx, nil)
	if err != nil {
		panic(exceptions.NewBusinessError("MongoDB Ping 失败", err.Error()))
	}

	MongoClient = client
	log.Println(fmt.Printf("MongoDB 连接成功\n"))
}

// GetMongoDatabase 获取 MongoDB 数据库实例
func GetMongoDatabase() *mongo.Database {
	dbName := Config.Database.MongoDB.Database
	return MongoClient.Database(dbName)
}

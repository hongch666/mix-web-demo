package config

import (
	"context"
	"fmt"
	"time"

	"go.mongodb.org/mongo-driver/mongo"
	"go.mongodb.org/mongo-driver/mongo/options"
)

var MongoClient *mongo.Client

func InitMongoDB() {
	// 从配置文件读取 MongoDB 连接信息
	mongoURI := Config.Database.MongoDB.Url
	if mongoURI == "" {
		mongoURI = "mongodb://127.0.0.1:27017" // 默认值
	}

	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	clientOptions := options.Client().ApplyURI(mongoURI)
	client, err := mongo.Connect(ctx, clientOptions)
	if err != nil {
		panic(fmt.Errorf("MongoDB 连接失败: %v", err))
	}

	// 验证连接
	err = client.Ping(ctx, nil)
	if err != nil {
		panic(fmt.Errorf("MongoDB Ping 失败: %v", err))
	}

	MongoClient = client
	fmt.Printf("✅ MongoDB 连接成功: %s\n", mongoURI)
}

// GetMongoDatabase 获取 MongoDB 数据库实例
func GetMongoDatabase() *mongo.Database {
	dbName := Config.Database.MongoDB.Database
	if dbName == "" {
		dbName = "demo" // 默认数据库名
	}
	return MongoClient.Database(dbName)
}

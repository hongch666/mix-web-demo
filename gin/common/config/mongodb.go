package config

import (
	"context"
	"fmt"
	"log"
	"time"

	"github.com/hongch666/mix-web-demo/gin/common/exceptions"

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
		log.Printf(MONGODB_CONNECTION_WITH_AUTH_MESSAGE, username, "***", host, port)
	} else {
		mongoURI = fmt.Sprintf("mongodb://%s:%s", host, port)
		log.Printf(MONGODB_CONNECTION_NO_AUTH_MESSAGE, host, port)
	}

	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	clientOptions := options.Client().ApplyURI(mongoURI)
	client, err := mongo.Connect(ctx, clientOptions)
	if err != nil {
		panic(exceptions.NewBusinessError(MONGODB_CONNECTION_FAILURE_MESSAGE, err.Error()))
	}

	// 验证连接
	err = client.Ping(ctx, nil)
	if err != nil {
		panic(exceptions.NewBusinessError(MONGODB_PING_FAILURE_MESSAGE, err.Error()))
	}

	MongoClient = client
	log.Println(MONGODB_CONNECTION_SUCCESS_MESSAGE)
}

// GetMongoDatabase 获取 MongoDB 数据库实例
func GetMongoDatabase() *mongo.Database {
	dbName := Config.Database.MongoDB.Database
	return MongoClient.Database(dbName)
}

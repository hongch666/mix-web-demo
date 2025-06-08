package config

import (
	"fmt"
	"log"
	"time"

	"github.com/streadway/amqp"
)

// RabbitMQ 客户端结构体
type RabbitMQClient struct {
	Conn    *amqp.Connection
	Channel *amqp.Channel
}

// 全局实例
var RabbitMQ *RabbitMQClient

// 初始化 RabbitMQ 连接（配置写死）
func InitRabbitMQ() {
	// 写死的连接信息
	username := "hcsy"
	password := "123456"
	host := "127.0.0.1"
	port := "5672"
	vhost := "test"

	url := fmt.Sprintf("amqp://%s:%s@%s:%s/%s", username, password, host, port, vhost)

	conn, err := amqp.Dial(url)
	if err != nil {
		log.Fatalf("RabbitMQ 连接失败: %v", err)
	}

	channel, err := conn.Channel()
	if err != nil {
		log.Fatalf("创建 Channel 失败: %v", err)
	}

	RabbitMQ = &RabbitMQClient{
		Conn:    conn,
		Channel: channel,
	}

	log.Println("✅ RabbitMQ 初始化成功")
}

// 发送消息到指定队列
func (r *RabbitMQClient) Send(queueName string, body string) error {
	// 声明队列（幂等）
	_, err := r.Channel.QueueDeclare(
		queueName,
		true,  // durable
		false, // autoDelete
		false, // exclusive
		false, // noWait
		nil,   // args
	)
	if err != nil {
		return err
	}

	// 发布消息
	err = r.Channel.Publish(
		"",        // default exchange
		queueName, // routing key
		false,
		false,
		amqp.Publishing{
			ContentType: "application/json",
			Body:        []byte(body),
			Timestamp:   time.Now(),
		},
	)
	if err != nil {
		return err
	}

	log.Printf("已发送到队列 [%s]: %s", queueName, body)
	return nil
}

// 关闭连接
func (r *RabbitMQClient) Close() {
	if r.Channel != nil {
		r.Channel.Close()
	}
	if r.Conn != nil {
		r.Conn.Close()
	}
	log.Println("RabbitMQ 连接已关闭")
}

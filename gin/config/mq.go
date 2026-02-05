package config

import (
	"fmt"
	"log"
	"time"

	amqp "github.com/rabbitmq/amqp091-go"
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
	username := Config.MQ.Username
	password := Config.MQ.Password
	host := Config.MQ.Host
	port := Config.MQ.Port
	vhost := Config.MQ.Vhost

	url := fmt.Sprintf("amqp://%s:%s@%s:%s/%s", username, password, host, port, vhost)

	conn, err := amqp.Dial(url)
	if err != nil {
		log.Fatalf(RABBITMQ_CONNECTION_FAILURE_MESSAGE, err)
	}

	channel, err := conn.Channel()
	if err != nil {
		log.Fatalf(RABBITMQ_CREATE_CHANNEL_FAILURE_MESSAGE, err)
	}

	RabbitMQ = &RabbitMQClient{
		Conn:    conn,
		Channel: channel,
	}

	// 初始化时自动创建使用的队列
	err = createQueues()
	if err != nil {
		log.Fatalf("Failed to create RabbitMQ queues: %v", err)
	}

	log.Println(RABBITMQ_INITIALIZATION_SUCCESS_MESSAGE)
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
		log.Printf(SEND_MESSAGE_TO_QUEUE_FAILURE_MESSAGE, queueName, err)
		return err
	}

	log.Printf(SEND_MESSAGE_TO_QUEUE_SUCCESS_MESSAGE, queueName, body)
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
	log.Println(CLOSE_RABBITMQ_CONNECTION_MESSAGE)
}

// createQueues 在初始化时创建所有使用的队列
func createQueues() error {
	queues := []string{
		"api-log-queue", // API日志队列，由api_log中间件使用
		"log-queue",     // 通用日志队列，由search服务使用
	}

	for _, queueName := range queues {
		_, err := RabbitMQ.Channel.QueueDeclare(
			queueName,
			true,  // durable - 队列持久化
			false, // autoDelete - 不自动删除
			false, // exclusive - 不独占
			false, // noWait - 等待确认
			nil,   // args - 额外参数
		)
		if err != nil {
			return fmt.Errorf("failed to declare queue %s: %w", queueName, err)
		}
		log.Printf("Queue '%s' declared successfully", queueName)
	}

	return nil
}

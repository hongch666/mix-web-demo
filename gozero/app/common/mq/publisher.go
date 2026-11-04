package mq

import (
	"encoding/json"
	"errors"
	"fmt"
	"time"

	"app/common/constants"

	rabbitmq "github.com/wagslane/go-rabbitmq"
)

// publisherCommander MQ 发布器依赖的最小命令集合，*rabbitmq.Publisher 直接满足，单测可用替身实现
type publisherCommander interface {
	// Publish 投递原始字节到指定路由
	Publish(data []byte, routingKeys []string, optionFuncs ...func(*rabbitmq.PublishOptions)) error
	// Close 关闭发布通道
	Close()
}

// Publisher RabbitMQ 消息发布器，负责 JSON 序列化与投递，nil 接收方或未初始化时投递返回错误
type Publisher struct {
	conn      *rabbitmq.Conn
	publisher publisherCommander
}

// NewPublisher 创建消息发布器并建立 AMQP 连接，url 为空时返回错误，连接失败时关闭已建资源后上抛
func NewPublisher(url string) (*Publisher, error) {
	if url == "" {
		return nil, errors.New(constants.MQ_AMQP_URL_EMPTY_ERROR)
	}

	conn, err := rabbitmq.NewConn(url)
	if err != nil {
		return nil, err
	}

	publisher, err := rabbitmq.NewPublisher(conn, rabbitmq.WithPublisherOptionsLogging)
	if err != nil {
		_ = conn.Close()
		return nil, err
	}

	return &Publisher{conn: conn, publisher: publisher}, nil
}

// PublishJSON 将 payload 序列化为 JSON 并投递到指定队列，queue 作为 default exchange 的 routingKey
func (p *Publisher) PublishJSON(queue string, payload any) error {
	if p == nil || p.publisher == nil {
		return fmt.Errorf(constants.MQ_PUBLISHER_NOT_INITIALIZED_ERROR)
	}

	data, err := json.Marshal(payload)
	if err != nil {
		return fmt.Errorf(constants.MQ_PUBLISH_SERIALIZE_ERROR, queue, err)
	}

	return p.publisher.Publish(data, []string{queue},
		rabbitmq.WithPublishOptionsContentType("application/json"),
		rabbitmq.WithPublishOptionsTimestamp(time.Now()),
	)
}

// Close 释放发布通道与底层 AMQP 连接，重复调用安全
func (p *Publisher) Close() {
	if p == nil {
		return
	}

	if p.publisher != nil {
		p.publisher.Close()
	}
	if p.conn != nil {
		_ = p.conn.Close()
	}
}

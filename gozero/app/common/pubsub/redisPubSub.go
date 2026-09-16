// Package pubsub 提供基于 Redis Pub/Sub 的跨实例消息总线
// 单个 RedisPubSub 实例对应单一频道，频道在构造时确定
package pubsub

import (
	"context"
	"fmt"
	"sync"
	"time"

	"app/common/constants"
	"app/common/utils"

	"github.com/redis/go-redis/v9"
)

// MessageHandler 处理跨实例实时消息
type MessageHandler func(payload []byte)

// RedisPubSub 基于 Redis Pub/Sub 的跨实例消息总线
// 每个实例只订阅并发布构造时绑定的那个频道
type RedisPubSub struct {
	client  *redis.Client
	logger  *utils.ZeroLogger
	channel string

	mu     sync.Mutex
	pubsub *redis.PubSub
	closed bool
}

// NewRedisPubSub 创建绑定到指定频道的 Redis 消息总线
func NewRedisPubSub(client *redis.Client, logger *utils.ZeroLogger, channel string) *RedisPubSub {
	return &RedisPubSub{client: client, logger: logger, channel: channel}
}

// Publish 向本实例绑定的频道发布一条消息
func (p *RedisPubSub) Publish(ctx context.Context, payload []byte) error {
	if p == nil || p.client == nil || p.channel == "" {
		return fmt.Errorf(constants.REDIS_REALTIME_BUS_NOT_INITIALIZED_ERROR)
	}
	return p.client.Publish(ctx, p.channel, payload).Err()
}

// Start 启动本实例绑定频道的订阅协程
func (p *RedisPubSub) Start(ctx context.Context, handler MessageHandler) {
	if p == nil || p.client == nil || p.channel == "" || handler == nil {
		return
	}
	go p.run(ctx, handler)
}

func (p *RedisPubSub) run(ctx context.Context, handler MessageHandler) {
	for {
		if ctx.Err() != nil || p.isClosed() {
			return
		}

		pubsub := p.client.Subscribe(ctx, p.channel)
		p.setPubSub(pubsub)
		if _, err := pubsub.Receive(ctx); err != nil {
			p.closeCurrentPubSub(pubsub)
			if ctx.Err() != nil || p.isClosed() {
				return
			}
			p.logError(fmt.Errorf(constants.REDIS_REALTIME_SUBSCRIBE_ERROR, err))
			if !waitForRetry(ctx) {
				return
			}
			continue
		}

		for {
			message, err := pubsub.ReceiveMessage(ctx)
			if err != nil {
				p.closeCurrentPubSub(pubsub)
				if ctx.Err() != nil || p.isClosed() {
					return
				}
				p.logError(fmt.Errorf(constants.REDIS_REALTIME_SUBSCRIBE_ERROR, err))
				break
			}
			handler([]byte(message.Payload))
		}

		if !waitForRetry(ctx) {
			return
		}
	}
}

// Close 停止订阅并关闭当前 Redis Pub/Sub 连接
func (p *RedisPubSub) Close() {
	if p == nil {
		return
	}

	p.mu.Lock()
	p.closed = true
	pubsub := p.pubsub
	p.pubsub = nil
	p.mu.Unlock()

	if pubsub != nil {
		_ = pubsub.Close()
	}
}

func (p *RedisPubSub) isClosed() bool {
	p.mu.Lock()
	defer p.mu.Unlock()
	return p.closed
}

func (p *RedisPubSub) setPubSub(pubsub *redis.PubSub) {
	p.mu.Lock()
	defer p.mu.Unlock()
	if p.closed {
		_ = pubsub.Close()
		return
	}
	p.pubsub = pubsub
}

func (p *RedisPubSub) closeCurrentPubSub(pubsub *redis.PubSub) {
	p.mu.Lock()
	if p.pubsub == pubsub {
		p.pubsub = nil
	}
	p.mu.Unlock()
	_ = pubsub.Close()
}

func (p *RedisPubSub) logError(err error) {
	if p.logger != nil {
		p.logger.Error(err.Error())
	}
}

func waitForRetry(ctx context.Context) bool {
	timer := time.NewTimer(time.Second)
	defer timer.Stop()
	select {
	case <-ctx.Done():
		return false
	case <-timer.C:
		return true
	}
}

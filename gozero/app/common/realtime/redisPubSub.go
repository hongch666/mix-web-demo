package realtime

import (
	"context"
	"fmt"
	"sync"
	"time"

	"app/common/constants"
	"app/common/utils"

	"github.com/redis/go-redis/v9"
)

// MessageHandler 处理跨 Pod 实时消息
type MessageHandler func(payload []byte)

// RedisPubSub 基于 Redis Pub/Sub 的实时消息总线
type RedisPubSub struct {
	client *redis.Client
	logger *utils.ZeroLogger

	mu     sync.Mutex
	pubsub *redis.PubSub
	closed bool
}

// NewRedisPubSub 创建 Redis 实时消息总线
func NewRedisPubSub(client *redis.Client, logger *utils.ZeroLogger) *RedisPubSub {
	return &RedisPubSub{client: client, logger: logger}
}

// Publish 发布一条跨 Pod 实时消息
func (p *RedisPubSub) Publish(ctx context.Context, payload []byte) error {
	if p == nil || p.client == nil {
		return fmt.Errorf(constants.REDIS_REALTIME_BUS_NOT_INITIALIZED_ERROR)
	}
	return p.client.Publish(ctx, constants.REALTIME_CHAT_CHANNEL, payload).Err()
}

// Start 启动 Redis 实时消息订阅协程
func (p *RedisPubSub) Start(ctx context.Context, handler MessageHandler) {
	if p == nil || p.client == nil || handler == nil {
		return
	}
	go p.run(ctx, handler)
}

func (p *RedisPubSub) run(ctx context.Context, handler MessageHandler) {
	for {
		if ctx.Err() != nil || p.isClosed() {
			return
		}

		pubsub := p.client.Subscribe(ctx, constants.REALTIME_CHAT_CHANNEL)
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

package redis

import (
	"context"
	"testing"

	goredis "github.com/redis/go-redis/v9"
)

// 未初始化的消息总线发布时必须返回错误，避免调用方误以为广播成功
func TestPubSubPublishRejectsUninitializedInstance(t *testing.T) {
	if err := (*PubSub)(nil).Publish(context.Background(), []byte("x")); err == nil {
		t.Fatal("nil 消息总线应返回未初始化错误")
	}
	if err := NewPubSub(nil, nil, "").Publish(context.Background(), []byte("x")); err == nil {
		t.Fatal("缺少客户端或频道时应返回未初始化错误")
	}
}

// 订阅入口对非法入参必须静默忽略，不产生协程
func TestPubSubStartIgnoresInvalidInputs(t *testing.T) {
	var nilPubSub *PubSub
	nilPubSub.Start(context.Background(), func([]byte) {})
	NewPubSub(nil, nil, "channel").Start(context.Background(), nil)
}

// Close 必须幂等，重复调用不应 panic
func TestPubSubCloseIsIdempotent(t *testing.T) {
	pubSub := NewPubSub(goredis.NewClient(&goredis.Options{Addr: "127.0.0.1:1"}), nil, "channel")
	pubSub.Close()
	pubSub.Close()
	if !pubSub.isClosed() {
		t.Fatal("Close 后应标记为已关闭")
	}
}

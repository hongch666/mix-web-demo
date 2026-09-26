package pubsub

import (
	"context"
	"testing"

	"github.com/redis/go-redis/v9"
)

func TestRedisPubSubPublishRejectsUninitializedInstance(t *testing.T) {
	if err := (*RedisPubSub)(nil).Publish(context.Background(), []byte("x")); err == nil {
		t.Fatal("nil pubsub should return initialization error")
	}
	if err := NewRedisPubSub(nil, nil, "").Publish(context.Background(), []byte("x")); err == nil {
		t.Fatal("missing client and channel should return initialization error")
	}
}

func TestRedisPubSubStartIgnoresInvalidInputs(t *testing.T) {
	var nilPubSub *RedisPubSub
	nilPubSub.Start(context.Background(), func([]byte) {})
	NewRedisPubSub(nil, nil, "channel").Start(context.Background(), nil)
}

func TestRedisPubSubCloseIsIdempotent(t *testing.T) {
	pubsub := NewRedisPubSub(redis.NewClient(&redis.Options{Addr: "127.0.0.1:1"}), nil, "channel")
	pubsub.Close()
	pubsub.Close()
	if !pubsub.isClosed() {
		t.Fatal("close should mark pubsub as closed")
	}
}

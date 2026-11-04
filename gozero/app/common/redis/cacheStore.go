package redis

import (
	"context"
	"errors"
	"time"

	"app/common/cache"

	goredis "github.com/redis/go-redis/v9"
)

// cacheCommander 两级缓存 L2 存储依赖的最小 Redis 命令集合，*redis.Client 直接满足，单测可用替身实现
type cacheCommander interface {
	// Get 读取字符串缓存
	Get(ctx context.Context, key string) *goredis.StringCmd
	// Set 写入字符串缓存并设置过期时间
	Set(ctx context.Context, key string, value any, expiration time.Duration) *goredis.StatusCmd
	// Del 删除缓存 key
	Del(ctx context.Context, keys ...string) *goredis.IntCmd
}

// CacheStore 基于 go-redis 的 L2 缓存实现，满足 cache.Store 契约
type CacheStore struct {
	client cacheCommander
}

// NewCacheStore 创建 L2 缓存存储适配器，client 为 nil 时返回 nil 表示不启用 L2 缓存
func NewCacheStore(client *goredis.Client) cache.Store {
	if client == nil {
		return nil
	}
	return &CacheStore{client: client}
}

// Get 读取缓存原始字节，key 不存在时返回 cache.ErrCacheMiss
func (s *CacheStore) Get(ctx context.Context, key string) ([]byte, error) {
	raw, err := s.client.Get(ctx, key).Bytes()
	if errors.Is(err, goredis.Nil) {
		return nil, cache.ErrCacheMiss
	}
	if err != nil {
		return nil, err
	}
	return raw, nil
}

// Set 写入缓存并设置过期时间，ttl 为 0 表示不过期
func (s *CacheStore) Set(ctx context.Context, key string, value []byte, ttl time.Duration) error {
	return s.client.Set(ctx, key, value, ttl).Err()
}

// Delete 删除缓存 key，key 不存在视为成功
func (s *CacheStore) Delete(ctx context.Context, keys ...string) error {
	if len(keys) == 0 {
		return nil
	}
	return s.client.Del(ctx, keys...).Err()
}

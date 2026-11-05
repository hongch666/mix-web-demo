package cache

import (
	"context"
	"encoding/json"
	"errors"
	"sync"
	"time"

	"app/common/constants"
	"app/common/utils"

	"github.com/zeromicro/go-zero/core/syncx"
)

// Loader 缓存未命中时的回源函数，返回值会被写入两级缓存
type Loader[T any] func(ctx context.Context) (T, error)

// Store L2 缓存的最小存储接口，Redis 实现在 common/redis 的 CacheStore，测试或其它存储可替换实现
type Store interface {
	// Get 读取缓存原始字节，未命中返回 ErrCacheMiss
	Get(ctx context.Context, key string) ([]byte, error)
	// Set 写入缓存并设置过期时间
	Set(ctx context.Context, key string, value []byte, ttl time.Duration) error
	// Delete 删除缓存 key，key 不存在视为成功
	Delete(ctx context.Context, keys ...string) error
}

// ErrCacheMiss L2 缓存未命中
var ErrCacheMiss = errors.New(constants.CACHE_MISS)

// TTL 两级缓存的有效期配置，由调用方按业务场景传入，未配置的项由默认值兜底
type TTL struct {
	// Local L1 本地缓存有效期
	Local time.Duration
	// Redis L2 Redis 缓存有效期
	Redis time.Duration
}

// Options 多级缓存配置，零值项回退到 constants 中的默认值
type Options struct {
	// KeyPrefix Redis key 前缀，用于隔离不同业务的缓存，空串表示直接使用业务 key
	KeyPrefix string
	// LocalTTL L1 本地缓存有效期
	LocalTTL time.Duration
	// RedisTTL L2 缓存有效期
	RedisTTL time.Duration
	// LocalMaxEntries L1 本地缓存最大条目数，超出后淘汰最早写入的条目
	LocalMaxEntries int
	// Store L2 缓存实现，nil 时退化为纯本地缓存
	Store Store
	// Logger 日志实例，nil 时静默
	Logger *utils.ZeroLogger
}

// localEntry L1 缓存条目，expiresAt 之后失效但仍可作为回源失败时的降级旧值
// seq 为写入序号，用于容量淘汰时确定最早写入的条目：时间戳在同一毫秒内的多条写入无法区分先后
type localEntry[T any] struct {
	value     T
	seq       uint64
	expiresAt time.Time
}

// MultiLevelCache 本地内存加 Redis 的两级缓存，支持并发回源合并、回源失败降级旧值与 L2 不可用退化
// 跨实例一致性由 TTL 保证：本实例的删除只影响自己的 L1，其它实例最迟在 L1 过期后失效
type MultiLevelCache[T any] struct {
	opts   Options
	flight syncx.SingleFlight

	mu      sync.RWMutex
	entries map[string]*localEntry[T]
	nextSeq uint64
}

// NewMultiLevelCache 创建两级缓存实例，未显式配置的 TTL、容量与日志回退到默认值
func NewMultiLevelCache[T any](opts Options) *MultiLevelCache[T] {
	if opts.LocalTTL <= 0 {
		opts.LocalTTL = constants.CACHE_LOCAL_TTL
	}
	if opts.RedisTTL <= 0 {
		opts.RedisTTL = constants.CACHE_REDIS_TTL
	}
	if opts.LocalMaxEntries <= 0 {
		opts.LocalMaxEntries = constants.CACHE_LOCAL_MAX_ENTRIES
	}

	return &MultiLevelCache[T]{
		opts:    opts,
		flight:  syncx.NewSingleFlight(),
		entries: make(map[string]*localEntry[T]),
	}
}

// Get 读取缓存，顺序为 L1 本地、L2 存储、回源函数；回源失败时降级返回本地旧值
func (c *MultiLevelCache[T]) Get(ctx context.Context, key string, loader Loader[T]) (T, error) {
	if value, ok := c.getLocal(key); ok {
		return value, nil
	}

	if value, ok := c.getStore(ctx, key); ok {
		c.setLocal(key, value)
		return value, nil
	}

	result, err := c.flight.Do(c.storeKey(key), func() (any, error) {
		// 并发请求被合并后重新检查缓存，前一个请求可能已经回填
		if value, ok := c.getLocal(key); ok {
			return value, nil
		}
		if value, ok := c.getStore(ctx, key); ok {
			c.setLocal(key, value)
			return value, nil
		}
		if loader == nil {
			return nil, errors.New(constants.CACHE_LOADER_MISSING)
		}

		value, err := loader(ctx)
		if err != nil {
			return nil, err
		}

		c.setLocal(key, value)
		c.setStore(ctx, key, value)
		return value, nil
	})
	if err != nil {
		if stale, ok := c.getStale(key); ok {
			c.logWarning(constants.CACHE_LOADER_FALLBACK_STALE, c.storeKey(key), err)
			return stale, nil
		}

		var zero T
		return zero, err
	}

	value, ok := result.(T)
	if !ok {
		var zero T
		return zero, errors.New(constants.CACHE_VALUE_TYPE_MISMATCH)
	}
	return value, nil
}

// Set 直接写入两级缓存，用于预热或外部回填
func (c *MultiLevelCache[T]) Set(ctx context.Context, key string, value T) {
	c.setLocal(key, value)
	c.setStore(ctx, key, value)
}

// Delete 删除两级缓存中的指定 key
func (c *MultiLevelCache[T]) Delete(ctx context.Context, key string) {
	c.mu.Lock()
	delete(c.entries, key)
	c.mu.Unlock()

	if c.opts.Store == nil {
		return
	}
	if err := c.opts.Store.Delete(ctx, c.storeKey(key)); err != nil {
		c.logWarning(constants.CACHE_L2_DELETE_ERROR, c.storeKey(key), err)
	}
}

// getLocal 读取未过期的本地缓存
func (c *MultiLevelCache[T]) getLocal(key string) (T, bool) {
	c.mu.RLock()
	entry, ok := c.entries[key]
	c.mu.RUnlock()

	if !ok || time.Now().After(entry.expiresAt) {
		var zero T
		return zero, false
	}
	return entry.value, true
}

// getStale 读取本地已有缓存，不校验过期时间，供回源失败时降级
func (c *MultiLevelCache[T]) getStale(key string) (T, bool) {
	c.mu.RLock()
	defer c.mu.RUnlock()

	entry, ok := c.entries[key]
	if !ok {
		var zero T
		return zero, false
	}
	return entry.value, true
}

// setLocal 写入本地缓存，容量超限时淘汰最早写入的条目
func (c *MultiLevelCache[T]) setLocal(key string, value T) {
	now := time.Now()

	c.mu.Lock()
	defer c.mu.Unlock()

	if _, exists := c.entries[key]; !exists && len(c.entries) >= c.opts.LocalMaxEntries {
		c.evictOldestLocked()
	}
	c.nextSeq++
	c.entries[key] = &localEntry[T]{
		value:     value,
		seq:       c.nextSeq,
		expiresAt: now.Add(c.opts.LocalTTL),
	}
}

// evictOldestLocked 淘汰最早写入的条目，调用方必须持有写锁
func (c *MultiLevelCache[T]) evictOldestLocked() {
	var oldestKey string
	var oldestSeq uint64

	for key, entry := range c.entries {
		if oldestKey == "" || entry.seq < oldestSeq {
			oldestKey = key
			oldestSeq = entry.seq
		}
	}

	if oldestKey != "" {
		delete(c.entries, oldestKey)
	}
}

// getStore 读取 L2 缓存并反序列化，未命中或读取失败都返回 false
func (c *MultiLevelCache[T]) getStore(ctx context.Context, key string) (T, bool) {
	var zero T
	if c.opts.Store == nil {
		return zero, false
	}

	storeKey := c.storeKey(key)
	raw, err := c.opts.Store.Get(ctx, storeKey)
	if err != nil {
		if !errors.Is(err, ErrCacheMiss) {
			c.logWarning(constants.CACHE_L2_READ_ERROR, storeKey, err)
		}
		return zero, false
	}

	var value T
	if err := json.Unmarshal(raw, &value); err != nil {
		c.logWarning(constants.CACHE_L2_DECODE_ERROR, storeKey, err)
		return zero, false
	}
	return value, true
}

// setStore 序列化并写入 L2 缓存，失败只记录日志
func (c *MultiLevelCache[T]) setStore(ctx context.Context, key string, value T) {
	if c.opts.Store == nil {
		return
	}

	raw, err := json.Marshal(value)
	if err != nil {
		c.logWarning(constants.CACHE_L2_ENCODE_ERROR, c.storeKey(key), err)
		return
	}

	if err := c.opts.Store.Set(ctx, c.storeKey(key), raw, c.opts.RedisTTL); err != nil {
		c.logWarning(constants.CACHE_L2_WRITE_ERROR, c.storeKey(key), err)
	}
}

// storeKey 拼接 L2 缓存完整 key
func (c *MultiLevelCache[T]) storeKey(key string) string {
	return c.opts.KeyPrefix + key
}

// logWarning 输出告警日志，未注入日志实例时静默
func (c *MultiLevelCache[T]) logWarning(format string, args ...any) {
	if c.opts.Logger == nil {
		return
	}
	c.opts.Logger.Warningf(format, args...)
}

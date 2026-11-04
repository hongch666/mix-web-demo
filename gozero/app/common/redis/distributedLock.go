package redis

import (
	"context"
	"fmt"
	"time"

	"app/common/constants"

	"github.com/google/uuid"
	goredis "github.com/redis/go-redis/v9"
)

// lockCommander 分布式锁依赖的最小 Redis 命令集合，*redis.Client 直接满足，单测可用替身实现
type lockCommander interface {
	// SetNX 仅当 key 不存在时写入，用于原子加锁
	SetNX(ctx context.Context, key string, value any, expiration time.Duration) *goredis.BoolCmd
	// Eval 执行 Lua 脚本，用于原子解锁
	Eval(ctx context.Context, script string, keys []string, args ...any) *goredis.Cmd
}

// DistributedLock Redis 分布式锁，使用 SET NX EX 实现原子加锁，Lua 脚本实现原子解锁
type DistributedLock struct {
	client lockCommander
}

// NewDistributedLock 创建 Redis 分布式锁实例
func NewDistributedLock(client *goredis.Client) *DistributedLock {
	return &DistributedLock{client: client}
}

// TryLock 尝试获取分布式锁，lockKey: 锁的 Redis key，expireSeconds: 锁的过期时间（秒），应大于任务执行时间，防止死锁，返回锁的唯一标识（UUID），获取失败返回空字符串
func (l *DistributedLock) TryLock(ctx context.Context, lockKey string, expireSeconds int64) (string, error) {
	lockValue := uuid.New().String()
	ok, err := l.client.SetNX(ctx, lockKey, lockValue, time.Duration(expireSeconds)*time.Second).Result()
	if err != nil {
		return "", fmt.Errorf(constants.REDIS_LOCK_ACQUIRE_ERROR, err)
	}
	if !ok {
		return "", nil
	}
	return lockValue, nil
}

// Unlock 释放分布式锁（原子操作，只有锁持有者才能解锁），lockKey: 锁的 Redis key，lockValue: 锁的唯一标识（加锁时返回的值）
func (l *DistributedLock) Unlock(ctx context.Context, lockKey, lockValue string) (bool, error) {
	result, err := l.client.Eval(ctx, constants.UNLOCK_LUA_SCRIPT, []string{lockKey}, lockValue).Int64()
	if err != nil {
		return false, fmt.Errorf(constants.REDIS_LOCK_RELEASE_ERROR, err)
	}
	return result == 1, nil
}

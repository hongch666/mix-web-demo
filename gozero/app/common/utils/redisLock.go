package utils

import (
	"context"
	"fmt"
	"time"

	"github.com/google/uuid"
	"github.com/redis/go-redis/v9"
)

// RedisDistributedLock Redis 分布式锁
// 使用 SET NX EX 实现原子加锁，Lua 脚本实现原子解锁
type RedisDistributedLock struct {
	client *redis.Client
}

// 解锁 Lua 脚本：只有当锁的值与预期值一致时才删除，保证只有锁持有者才能解锁
const unlockScript = `
if redis.call("get", KEYS[1]) == ARGV[1] then
	return redis.call("del", KEYS[1])
else
	return 0
end
`

// NewRedisDistributedLock 创建 Redis 分布式锁实例
func NewRedisDistributedLock(client *redis.Client) *RedisDistributedLock {
	return &RedisDistributedLock{client: client}
}

// TryLock 尝试获取分布式锁
// lockKey: 锁的 Redis key
// expireSeconds: 锁的过期时间（秒），应大于任务执行时间，防止死锁
// 返回锁的唯一标识（UUID），获取失败返回空字符串
func (l *RedisDistributedLock) TryLock(ctx context.Context, lockKey string, expireSeconds int64) (string, error) {
	lockValue := uuid.New().String()
	ok, err := l.client.SetNX(ctx, lockKey, lockValue, time.Duration(expireSeconds)*time.Second).Result()
	if err != nil {
		return "", fmt.Errorf(REDIS_LOCK_ACQUIRE_ERROR, err)
	}
	if !ok {
		return "", nil
	}
	return lockValue, nil
}

// Unlock 释放分布式锁（原子操作，只有锁持有者才能解锁）
// lockKey: 锁的 Redis key
// lockValue: 锁的唯一标识（加锁时返回的值）
func (l *RedisDistributedLock) Unlock(ctx context.Context, lockKey, lockValue string) (bool, error) {
	result, err := l.client.Eval(ctx, unlockScript, []string{lockKey}, lockValue).Int64()
	if err != nil {
		return false, fmt.Errorf(REDIS_LOCK_RELEASE_ERROR, err)
	}
	return result == 1, nil
}

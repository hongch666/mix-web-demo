package com.hcsy.spring.common.utils;

import java.util.Collections;
import java.util.UUID;
import java.util.concurrent.TimeUnit;

import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.data.redis.core.script.DefaultRedisScript;
import org.springframework.stereotype.Component;

import lombok.RequiredArgsConstructor;

/**
 * Redis 分布式锁工具类
 * 使用 SET NX EX 实现原子加锁，Lua 脚本实现原子解锁
 */
@Component
@RequiredArgsConstructor
public class RedisDistributedLock {

    private final StringRedisTemplate redisTemplate;

    /**
     * 解锁 Lua 脚本：只有当锁的值与预期值一致时才删除，保证只有锁持有者才能解锁
     */
    private static final String UNLOCK_SCRIPT = "if redis.call('get', KEYS[1]) == ARGV[1] then " +
            "return redis.call('del', KEYS[1]) " +
            "else " +
            "return 0 " +
            "end";

    private static final DefaultRedisScript<Long> UNLOCK_REDIS_SCRIPT = new DefaultRedisScript<>(UNLOCK_SCRIPT,
            Long.class);

    /**
     * 尝试获取分布式锁
     *
     * @param lockKey       锁的 Redis key
     * @param expireSeconds 锁的过期时间（秒），应大于任务执行时间，防止死锁
     * @return 锁的唯一标识（UUID），获取失败返回 null
     */
    @SuppressWarnings("null")
    public String tryLock(String lockKey, long expireSeconds) {
        String lockValue = UUID.randomUUID().toString();
        Boolean success = redisTemplate.opsForValue().setIfAbsent(lockKey, lockValue, expireSeconds, TimeUnit.SECONDS);
        return Boolean.TRUE.equals(success) ? lockValue : null;
    }

    /**
     * 释放分布式锁（原子操作，只有锁持有者才能解锁）
     *
     * @param lockKey   锁的 Redis key
     * @param lockValue 锁的唯一标识（加锁时返回的值）
     * @return 是否成功释放
     */
    @SuppressWarnings("null")
    public boolean unlock(String lockKey, String lockValue) {
        Long result = redisTemplate.execute(UNLOCK_REDIS_SCRIPT,
                Collections.singletonList(lockKey), lockValue);
        return Long.valueOf(1L).equals(result);
    }
}

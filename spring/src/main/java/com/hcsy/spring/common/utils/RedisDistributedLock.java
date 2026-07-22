package com.hcsy.spring.common.utils;

import java.time.Duration;
import java.util.List;
import java.util.UUID;

import org.springframework.data.redis.core.ReactiveStringRedisTemplate;
import org.springframework.data.redis.core.script.RedisScript;
import org.springframework.stereotype.Component;

import lombok.RequiredArgsConstructor;
import reactor.core.publisher.Mono;

/**
 * Redis 响应式分布式锁
 */
@Component
@RequiredArgsConstructor
public class RedisDistributedLock {

    private static final RedisScript<Long> UNLOCK_SCRIPT = RedisScript.of(
            "if redis.call('get', KEYS[1]) == ARGV[1] then return redis.call('del', KEYS[1]) else return 0 end",
            Long.class);

    private final ReactiveStringRedisTemplate redisTemplate;

    @SuppressWarnings("null")
    public Mono<String> tryLock(String lockKey, long expireSeconds) {
        String lockValue = UUID.randomUUID().toString();
        return redisTemplate.opsForValue()
                .setIfAbsent(lockKey, lockValue, Duration.ofSeconds(expireSeconds))
                .filter(Boolean.TRUE::equals)
                .map(ignored -> lockValue);
    }

    @SuppressWarnings("null")
    public Mono<Boolean> unlock(String lockKey, String lockValue) {
        return redisTemplate.execute(UNLOCK_SCRIPT, List.of(lockKey), List.of(lockValue))
                .next()
                .map(result -> result == 1L)
                .defaultIfEmpty(false);
    }
}

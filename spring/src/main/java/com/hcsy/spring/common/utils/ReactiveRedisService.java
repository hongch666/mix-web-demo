package com.hcsy.spring.common.utils;

import java.time.Duration;
import java.util.List;

import org.springframework.data.redis.core.ReactiveRedisTemplate;
import org.springframework.data.redis.core.script.RedisScript;
import org.springframework.stereotype.Component;

import lombok.RequiredArgsConstructor;
import reactor.core.publisher.Mono;

/**
 * 响应式 Redis 服务
 * 替代原有的阻塞式 RedisUtil，提供响应式操作
 */
@Component
@RequiredArgsConstructor
public class ReactiveRedisService {

    private final ReactiveRedisTemplate<String, Object> reactiveRedisTemplate;

    @SuppressWarnings("null")
    public Mono<String> get(String key) {
        return reactiveRedisTemplate.opsForValue().get(key)
            .map(Object::toString);
    }

    @SuppressWarnings("null")
    public Mono<Boolean> set(String key, String value, Duration ttl) {
        return reactiveRedisTemplate.opsForValue().set(key, value, ttl);
    }

    @SuppressWarnings("null")
    public Mono<Boolean> set(String key, String value) {
        return reactiveRedisTemplate.opsForValue().set(key, value);
    }

    public Mono<Boolean> delete(String key) {
        return reactiveRedisTemplate.delete(key).map(count -> count > 0);
    }

    @SuppressWarnings("null")
    public Mono<Boolean> expire(String key, Duration ttl) {
        return reactiveRedisTemplate.expire(key, ttl);
    }

    @SuppressWarnings("null")
    public Mono<Boolean> exists(String key) {
        return reactiveRedisTemplate.hasKey(key);
    }

    // ========== List 操作 ==========

    @SuppressWarnings("null")
    public Mono<Long> addToList(String key, String value) {
        return reactiveRedisTemplate.opsForList().rightPush(key, value);
    }

    @SuppressWarnings("null")
    public Mono<Long> removeFromList(String key, String value) {
        return reactiveRedisTemplate.opsForList().remove(key, 1, value);
    }

    @SuppressWarnings("null")
    public Mono<List<Object>> getList(String key) {
        return reactiveRedisTemplate.opsForList().range(key, 0, -1).collectList();
    }

    @SuppressWarnings("null")
    public Mono<Long> getListSize(String key) {
        return reactiveRedisTemplate.opsForList().size(key);
    }

    // ========== Hash 操作 ==========

    @SuppressWarnings("null")
    public Mono<Boolean> putHash(String key, String hashKey, String value) {
        return reactiveRedisTemplate.opsForHash().put(key, hashKey, value);
    }

    @SuppressWarnings("null")
    public Mono<Object> getHash(String key, String hashKey) {
        return reactiveRedisTemplate.opsForHash().get(key, hashKey);
    }

    @SuppressWarnings("null")
    public Mono<java.util.Map<Object, Object>> getHashEntries(String key) {
        return reactiveRedisTemplate.opsForHash().entries(key).collectMap(
            entry -> entry.getKey(),
            entry -> entry.getValue()
        );
    }

    @SuppressWarnings("null")
    public Mono<Long> deleteHash(String key, String... hashKeys) {
        return reactiveRedisTemplate.opsForHash().remove(key, (Object[]) hashKeys);
    }

    // ========== Set 操作 ==========

    @SuppressWarnings("null")
    public Mono<Long> addToSet(String key, String value) {
        return reactiveRedisTemplate.opsForSet().add(key, value);
    }

    @SuppressWarnings("null")
    public Mono<Long> removeFromSet(String key, String value) {
        return reactiveRedisTemplate.opsForSet().remove(key, value);
    }

    @SuppressWarnings("null")
    public Mono<java.util.Set<Object>> getSet(String key) {
        return reactiveRedisTemplate.opsForSet().members(key).collect(java.util.stream.Collectors.toSet());
    }

    @SuppressWarnings("null")
    public Mono<Long> getSetSize(String key) {
        return reactiveRedisTemplate.opsForSet().size(key);
    }

    // ========== 分布式锁 ==========

    @SuppressWarnings("null")
    public Mono<Boolean> tryLock(String key, String value, Duration ttl) {
        return reactiveRedisTemplate.opsForValue().setIfAbsent(key, value, ttl);
    }

    @SuppressWarnings("null")
    public Mono<Boolean> releaseLock(String key, String value) {
        String script = "if redis.call('get', KEYS[1]) == ARGV[1] then return redis.call('del', KEYS[1]) else return 0 end";
        return reactiveRedisTemplate.execute(
            RedisScript.of(script, Boolean.class), List.of(key), List.of(value)
        ).single();
    }

    // ========== Keys ==========

    @SuppressWarnings("null")
    public Mono<java.util.Set<String>> keys(String pattern) {
        return reactiveRedisTemplate.keys(pattern).collect(java.util.stream.Collectors.toSet());
    }
}

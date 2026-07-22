package com.hcsy.spring.common.utils;

import java.time.Duration;
import java.util.List;
import java.util.Map;

import org.springframework.data.redis.core.ReactiveStringRedisTemplate;
import org.springframework.data.redis.core.ScanOptions;
import org.springframework.stereotype.Component;

import lombok.RequiredArgsConstructor;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

/**
 * Redis 响应式工具类。
 */
@Component
@RequiredArgsConstructor
public class RedisUtil {

    private final ReactiveStringRedisTemplate redisTemplate;

    @SuppressWarnings("null")
    public Mono<Boolean> set(String key, String value, long timeoutSeconds) {
        return redisTemplate.opsForValue().set(key, value, Duration.ofSeconds(timeoutSeconds));
    }

    @SuppressWarnings("null")
    public Mono<Boolean> set(String key, String value) {
        return redisTemplate.opsForValue().set(key, value);
    }

    @SuppressWarnings("null")
    public Mono<String> get(String key) {
        return redisTemplate.opsForValue().get(key);
    }

    public Mono<List<String>> batchGet(List<String> keys) {
        if (keys == null || keys.isEmpty()) {
            return Mono.just(List.of());
        }
        return redisTemplate.opsForValue().multiGet(keys);
    }

    public Mono<Boolean> delete(String key) {
        return redisTemplate.delete(key).map(count -> count > 0);
    }

    @SuppressWarnings("null")
    public Mono<Long> delete(Iterable<String> keys) {
        return redisTemplate.delete(Flux.fromIterable(keys));
    }

    @SuppressWarnings("null")
    public Mono<Boolean> expire(String key, long timeoutSeconds) {
        return redisTemplate.expire(key, Duration.ofSeconds(timeoutSeconds));
    }

    @SuppressWarnings("null")
    public Mono<Long> addToList(String key, String value) {
        return redisTemplate.opsForList().rightPush(key, value);
    }

    @SuppressWarnings("null")
    public Mono<Long> removeFromList(String key, String value) {
        return redisTemplate.opsForList().remove(key, 1, value);
    }

    @SuppressWarnings("null")
    public Mono<List<String>> getList(String key) {
        return redisTemplate.opsForList().range(key, 0, -1).collectList();
    }

    @SuppressWarnings("null")
    public Mono<Long> getListSize(String key) {
        return redisTemplate.opsForList().size(key).defaultIfEmpty(0L);
    }

    public Mono<Boolean> clearList(String key) {
        return delete(key);
    }

    public Mono<Boolean> existsInList(String key, String value) {
        return getList(key).map(values -> values.contains(value));
    }

    @SuppressWarnings("null")
    public Flux<String> getKeys(String pattern) {
        return redisTemplate.scan(ScanOptions.scanOptions().match(pattern).count(200).build());
    }

    @SuppressWarnings("null")
    public Mono<Boolean> putHash(String key, String hashKey, String value) {
        return redisTemplate.opsForHash().put(key, hashKey, value);
    }

    @SuppressWarnings("null")
    public Mono<String> getHash(String key, String hashKey) {
        return redisTemplate.<String, String>opsForHash().get(key, hashKey);
    }

    @SuppressWarnings("null")
    public Mono<Map<String, String>> getHashEntries(String key) {
        return redisTemplate.<String, String>opsForHash().entries(key).collectMap(Map.Entry::getKey,
                Map.Entry::getValue);
    }

    @SuppressWarnings("null")
    public Mono<Long> deleteHash(String key, String... hashKeys) {
        return redisTemplate.<String, String>opsForHash().remove(key, (Object[]) hashKeys);
    }

    @SuppressWarnings("null")
    public Mono<Boolean> exists(String key) {
        return redisTemplate.hasKey(key);
    }

    @SuppressWarnings("null")
    public Mono<Long> addToSet(String key, String value) {
        return redisTemplate.opsForSet().add(key, value);
    }

    @SuppressWarnings("null")
    public Mono<Long> removeFromSet(String key, String value) {
        return redisTemplate.opsForSet().remove(key, value);
    }

    @SuppressWarnings("null")
    public Mono<List<String>> getSet(String key) {
        return redisTemplate.opsForSet().members(key).collectList();
    }

    @SuppressWarnings("null")
    public Mono<Long> getSetSize(String key) {
        return redisTemplate.opsForSet().size(key).defaultIfEmpty(0L);
    }
}

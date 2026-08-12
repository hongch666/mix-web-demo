package com.hcsy.gateway.utils;

import java.time.Duration;
import java.util.List;
import java.util.Map;

import org.springframework.data.redis.core.ReactiveStringRedisTemplate;
import org.springframework.data.redis.core.ScanOptions;
import org.springframework.stereotype.Component;

import lombok.RequiredArgsConstructor;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

@Component
@RequiredArgsConstructor
public class RedisUtil {

    private final ReactiveStringRedisTemplate redisTemplate;

    public Mono<Boolean> set(String key, String value, long timeoutSeconds) {
        return redisTemplate.opsForValue().set(key, value, Duration.ofSeconds(timeoutSeconds));
    }

    public Mono<Boolean> set(String key, String value) {
        return redisTemplate.opsForValue().set(key, value);
    }

    public Mono<String> get(String key) {
        return redisTemplate.opsForValue().get(key);
    }

    public Mono<Boolean> delete(String key) {
        return redisTemplate.delete(key).map(count -> count > 0);
    }

    public Mono<Boolean> expire(String key, long timeoutSeconds) {
        return redisTemplate.expire(key, Duration.ofSeconds(timeoutSeconds));
    }

    public Mono<Long> addToList(String key, String value) {
        return redisTemplate.opsForList().rightPush(key, value);
    }

    public Mono<Long> removeFromList(String key, String value) {
        return redisTemplate.opsForList().remove(key, 1, value);
    }

    public Mono<List<String>> getList(String key) {
        return redisTemplate.opsForList().range(key, 0, -1).collectList();
    }

    public Mono<Long> getListSize(String key) {
        return redisTemplate.opsForList().size(key).defaultIfEmpty(0L);
    }

    public Mono<Boolean> clearList(String key) {
        return delete(key);
    }

    public Mono<Boolean> existsInList(String key, String value) {
        return getList(key).map(values -> values.contains(value));
    }

    public Flux<String> getKeys(String pattern) {
        return redisTemplate.scan(ScanOptions.scanOptions().match(pattern).count(200).build());
    }

    public Mono<Boolean> exists(String key) {
        return redisTemplate.hasKey(key);
    }

    public Mono<Boolean> putHash(String key, String hashKey, String value) {
        return redisTemplate.opsForHash().put(key, hashKey, value);
    }

    public Mono<String> getHash(String key, String hashKey) {
        return redisTemplate.<String, String>opsForHash().get(key, hashKey);
    }

    public Mono<Map<String, String>> getHashEntries(String key) {
        return redisTemplate.<String, String>opsForHash().entries(key)
            .collectMap(Map.Entry::getKey, Map.Entry::getValue);
    }
}

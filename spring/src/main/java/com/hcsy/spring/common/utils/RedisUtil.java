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
 * Redis 响应式工具类
 */
@Component
@RequiredArgsConstructor
public class RedisUtil {

    private final ReactiveStringRedisTemplate redisTemplate;

    /**
     * 写入带过期时间的字符串键值
     */
    public Mono<Boolean> set(String key, String value, long timeoutSeconds) {
        return redisTemplate.opsForValue().set(key, value, Duration.ofSeconds(timeoutSeconds));
    }

    /**
     * 写入不过期的字符串键值
     */
    public Mono<Boolean> set(String key, String value) {
        return redisTemplate.opsForValue().set(key, value);
    }

    /**
     * 读取字符串键值
     */
    public Mono<String> get(String key) {
        return redisTemplate.opsForValue().get(key);
    }

    /**
     * 批量读取多个字符串键值
     */
    public Mono<List<String>> batchGet(List<String> keys) {
        if (keys == null || keys.isEmpty()) {
            return Mono.just(List.of());
        }
        return redisTemplate.opsForValue().multiGet(keys);
    }

    /**
     * 删除单个 key 并返回是否删除成功
     */
    public Mono<Boolean> delete(String key) {
        return redisTemplate.delete(key).map(count -> count > 0);
    }

    /**
     * 向 Redis 频道发布消息
     */
    public Mono<Long> publish(String channel, String message) {
        return redisTemplate.convertAndSend(channel, message);
    }

    /**
     * 批量删除多个 key 并返回删除数量
     */
    public Mono<Long> delete(Iterable<String> keys) {
        return redisTemplate.delete(Flux.fromIterable(keys));
    }

    /**
     * 设置 key 的过期时间
     */
    public Mono<Boolean> expire(String key, long timeoutSeconds) {
        return redisTemplate.expire(key, Duration.ofSeconds(timeoutSeconds));
    }

    /**
     * 向列表尾部追加元素
     */
    public Mono<Long> addToList(String key, String value) {
        return redisTemplate.opsForList().rightPush(key, value);
    }

    /**
     * 从列表中移除首个匹配的元素
     */
    public Mono<Long> removeFromList(String key, String value) {
        return redisTemplate.opsForList().remove(key, 1, value);
    }

    /**
     * 读取列表全部元素
     */
    public Mono<List<String>> getList(String key) {
        return redisTemplate.opsForList().range(key, 0, -1).collectList();
    }

    /**
     * 返回列表长度
     */
    public Mono<Long> getListSize(String key) {
        return redisTemplate.opsForList().size(key).defaultIfEmpty(0L);
    }

    /**
     * 删除整个列表
     */
    public Mono<Boolean> clearList(String key) {
        return delete(key);
    }

    /**
     * 判断值是否存在于列表中
     */
    public Mono<Boolean> existsInList(String key, String value) {
        return getList(key).map(values -> values.contains(value));
    }

    /**
     * 按 pattern SCAN 返回匹配的 key
     */
    public Flux<String> getKeys(String pattern) {
        return redisTemplate.scan(ScanOptions.scanOptions().match(pattern).count(200).build());
    }

    /**
     * 写入哈希字段的值
     */
    public Mono<Boolean> putHash(String key, String hashKey, String value) {
        return redisTemplate.opsForHash().put(key, hashKey, value);
    }

    /**
     * 读取哈希字段的值
     */
    public Mono<String> getHash(String key, String hashKey) {
        return redisTemplate.<String, String>opsForHash().get(key, hashKey);
    }

    /**
     * 读取哈希全部字段与值
     */
    public Mono<Map<String, String>> getHashEntries(String key) {
        return redisTemplate.<String, String>opsForHash().entries(key).collectMap(Map.Entry::getKey,
            Map.Entry::getValue);
    }

    /**
     * 删除哈希指定字段
     */
    public Mono<Long> deleteHash(String key, String... hashKeys) {
        return redisTemplate.<String, String>opsForHash().remove(key, (Object[]) hashKeys);
    }

    /**
     * 判断 key 是否存在
     */
    public Mono<Boolean> exists(String key) {
        return redisTemplate.hasKey(key);
    }

    /**
     * 向集合添加元素
     */
    public Mono<Long> addToSet(String key, String value) {
        return redisTemplate.opsForSet().add(key, value);
    }

    /**
     * 从集合移除元素
     */
    public Mono<Long> removeFromSet(String key, String value) {
        return redisTemplate.opsForSet().remove(key, value);
    }

    /**
     * 读取集合全部成员
     */
    public Mono<List<String>> getSet(String key) {
        return redisTemplate.opsForSet().members(key).collectList();
    }

    /**
     * 返回集合大小
     */
    public Mono<Long> getSetSize(String key) {
        return redisTemplate.opsForSet().size(key).defaultIfEmpty(0L);
    }
}

package com.hcsy.spring.common.utils;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.concurrent.TimeUnit;

import org.springframework.data.redis.core.RedisCallback;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.data.redis.serializer.StringRedisSerializer;
import org.springframework.stereotype.Component;

import lombok.RequiredArgsConstructor;

@Component
@RequiredArgsConstructor
public class RedisUtil {

    private final StringRedisTemplate redisTemplate;

    // 设置带过期时间的值
    @SuppressWarnings("null")
    public void set(String key, String value, long timeoutSeconds) {
        redisTemplate.opsForValue().set(key, value, timeoutSeconds, TimeUnit.SECONDS);
    }

    // 设置永久不过期的值
    @SuppressWarnings("null")
    public void set(String key, String value) {
        redisTemplate.opsForValue().set(key, value);
    }

    // 获取值
    @SuppressWarnings("null")
    public String get(String key) {
        return redisTemplate.opsForValue().get(key);
    }

    // 批量获取值，保持返回顺序与入参一致
    public List<String> batchGet(List<String> keys) {
        if (keys == null || keys.isEmpty()) {
            return new ArrayList<>();
        }

        StringRedisSerializer serializer = new StringRedisSerializer();
        List<Object> results = redisTemplate.executePipelined((RedisCallback<Object>) connection -> {
            for (String key : keys) {
                if (key != null) {
                    byte[] rawKey = serializer.serialize(key);
                    if (rawKey != null) {
                        connection.stringCommands().get(rawKey);
                    }
                }
            }
            return null;
        });

        List<String> values = new ArrayList<>(results.size());
        for (Object result : results) {
            values.add(Objects.toString(result, null));
        }
        return values;
    }

    // 删除值
    @SuppressWarnings("null")
    public void delete(String key) {
        redisTemplate.delete(key);
    }

    // 设置过期时间
    @SuppressWarnings("null")
    public void expire(String key, long timeoutSeconds) {
        redisTemplate.expire(key, timeoutSeconds, TimeUnit.SECONDS);
    }

    // 添加元素到列表末尾
    @SuppressWarnings("null")
    public void addToList(String key, String value) {
        redisTemplate.opsForList().rightPush(key, value);
    }

    // 从列表中移除指定元素
    @SuppressWarnings("null")
    public void removeFromList(String key, String value) {
        redisTemplate.opsForList().remove(key, 1, value);
    }

    // 获取列表所有元素
    @SuppressWarnings("null")
    public List<String> getList(String key) {
        Long size = redisTemplate.opsForList().size(key);
        if (size == null || size == 0) {
            return new ArrayList<>();
        }
        return redisTemplate.opsForList().range(key, 0, -1);
    }

    // 获取列表大小
    @SuppressWarnings("null")
    public long getListSize(String key) {
        Long size = redisTemplate.opsForList().size(key);
        return size != null ? size : 0;
    }

    // 清空列表
    @SuppressWarnings("null")
    public void clearList(String key) {
        redisTemplate.delete(key);
    }

    // 检查元素是否在列表中
    public boolean existsInList(String key, String value) {
        List<String> list = getList(key);
        return list.contains(value);
    }

    // 获取所有匹配 pattern 的 key
    @SuppressWarnings("null")
    public Set<String> getKeys(String pattern) {
        return redisTemplate.keys(pattern);
    }

    // ========== Hash 操作 ==========

    @SuppressWarnings("null")
    public void putHash(String key, String hashKey, String value) {
        redisTemplate.opsForHash().put(key, hashKey, value);
    }

    @SuppressWarnings("null")
    public String getHash(String key, String hashKey) {
        Object value = redisTemplate.opsForHash().get(key, hashKey);
        return value != null ? value.toString() : null;
    }

    @SuppressWarnings("null")
    public Map<Object, Object> getHashEntries(String key) {
        return redisTemplate.opsForHash().entries(key);
    }

    @SuppressWarnings("null")
    public void deleteHash(String key, String... hashKeys) {
        redisTemplate.opsForHash().delete(key, (Object[]) hashKeys);
    }

    @SuppressWarnings("null")
    public boolean exists(String key) {
        return Boolean.TRUE.equals(redisTemplate.hasKey(key));
    }

    // ========== Set 操作 ==========

    @SuppressWarnings("null")
    public void addToSet(String key, String value) {
        redisTemplate.opsForSet().add(key, value);
    }

    @SuppressWarnings("null")
    public void removeFromSet(String key, String value) {
        redisTemplate.opsForSet().remove(key, value);
    }

    @SuppressWarnings("null")
    public Set<String> getSet(String key) {
        return redisTemplate.opsForSet().members(key);
    }

    @SuppressWarnings("null")
    public long getSetSize(String key) {
        Long size = redisTemplate.opsForSet().size(key);
        return size != null ? size : 0;
    }
}

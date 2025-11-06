package com.hcsy.gateway.utils;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Component;

import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import java.util.concurrent.TimeUnit;

@Component
public class RedisUtil {

    @Autowired
    private StringRedisTemplate redisTemplate;

    // 设置带过期时间的值
    public void set(String key, String value, long timeoutSeconds) {
        redisTemplate.opsForValue().set(key, value, timeoutSeconds, TimeUnit.SECONDS);
    }

    // 设置永久不过期的值
    public void set(String key, String value) {
        redisTemplate.opsForValue().set(key, value);
    }

    // 获取值
    public String get(String key) {
        return redisTemplate.opsForValue().get(key);
    }

    // 删除值
    public void delete(String key) {
        redisTemplate.delete(key);
    }

    // 设置过期时间
    public void expire(String key, long timeoutSeconds) {
        redisTemplate.expire(key, timeoutSeconds, TimeUnit.SECONDS);
    }

    // ========== 列表操作 ==========

    /**
     * 添加元素到列表末尾
     */
    public void addToList(String key, String value) {
        redisTemplate.opsForList().rightPush(key, value);
    }

    /**
     * 从列表中移除指定元素
     */
    public void removeFromList(String key, String value) {
        redisTemplate.opsForList().remove(key, 1, value);
    }

    /**
     * 获取列表所有元素
     */
    public List<String> getList(String key) {
        Long size = redisTemplate.opsForList().size(key);
        if (size == null || size == 0) {
            return new ArrayList<>();
        }
        return redisTemplate.opsForList().range(key, 0, -1);
    }

    /**
     * 获取列表大小
     */
    public long getListSize(String key) {
        Long size = redisTemplate.opsForList().size(key);
        return size != null ? size : 0;
    }

    /**
     * 清空列表
     */
    public void clearList(String key) {
        redisTemplate.delete(key);
    }

    /**
     * 检查元素是否在列表中
     */
    public boolean existsInList(String key, String value) {
        List<String> list = getList(key);
        return list.contains(value);
    }

    /**
     * 获取所有匹配 pattern 的 key
     */
    public Set<String> getKeys(String pattern) {
        return redisTemplate.keys(pattern);
    }

    /**
     * 检查 key 是否存在
     */
    public boolean exists(String key) {
        return Boolean.TRUE.equals(redisTemplate.hasKey(key));
    }
}

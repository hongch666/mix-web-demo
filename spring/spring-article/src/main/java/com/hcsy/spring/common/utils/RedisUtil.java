package com.hcsy.spring.common.utils;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Component;

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
}

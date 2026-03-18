package com.hcsy.gateway.utils;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.data.redis.core.script.DefaultRedisScript;
import org.springframework.stereotype.Component;

import java.util.Arrays;
import java.util.List;
import java.util.Objects;

/**
 * Redis令牌桶限流器
 * 使用Lua脚本实现原子性操作
 */
@Component
@Slf4j
@RequiredArgsConstructor
public class TokenBucketRateLimiter {

    private final RedisTemplate<String, String> redisTemplate;

    /**
     * Lua脚本：实现令牌桶算法
     * KEYS[1]: 令牌桶key
     * ARGV[1]: 当前时间戳(毫秒)
     * ARGV[2]: 令牌桶容量
     * ARGV[3]: 令牌填充速率(每秒)
     */
    private static final String TOKEN_BUCKET_LUA_SCRIPT =
            "local bucket_key = KEYS[1]\n" +
            "local now = tonumber(ARGV[1])\n" +
            "local capacity = tonumber(ARGV[2])\n" +
            "local refill_rate = tonumber(ARGV[3])\n" +
            "\n" +
            "-- 获取上次填充时间和当前令牌数\n" +
            "local last_refill_time = redis.call('HGET', bucket_key, 'last_refill_time')\n" +
            "local current_tokens = redis.call('HGET', bucket_key, 'tokens')\n" +
            "\n" +
            "-- 初始化\n" +
            "if not last_refill_time then\n" +
            "    redis.call('HSET', bucket_key, 'last_refill_time', now)\n" +
            "    redis.call('HSET', bucket_key, 'tokens', capacity)\n" +
            "    redis.call('EXPIRE', bucket_key, 86400)\n" +
            "    return {1, capacity}\n" +
            "end\n" +
            "\n" +
            "last_refill_time = tonumber(last_refill_time)\n" +
            "current_tokens = tonumber(current_tokens)\n" +
            "\n" +
            "-- 计算应该添加的令牌数\n" +
            "local time_passed = math.max(0, (now - last_refill_time) / 1000)\n" +
            "local tokens_to_add = math.floor(time_passed * refill_rate)\n" +
            "local new_tokens = math.min(capacity, current_tokens + tokens_to_add)\n" +
            "\n" +
            "-- 更新令牌数和上次填充时间\n" +
            "redis.call('HSET', bucket_key, 'tokens', new_tokens)\n" +
            "redis.call('HSET', bucket_key, 'last_refill_time', now)\n" +
            "redis.call('EXPIRE', bucket_key, 86400)\n" +
            "\n" +
            "-- 检查是否有可用令牌\n" +
            "if new_tokens >= 1 then\n" +
            "    redis.call('HSET', bucket_key, 'tokens', new_tokens - 1)\n" +
            "    return {1, new_tokens - 1}\n" +
            "else\n" +
            "    return {0, new_tokens}\n" +
            "end\n";

    /**
     * 判断请求是否在限流范围内
     * @param key 限流key（通常为路径或用户标识）
     * @param capacity 令牌桶容量
     * @param refillRate 令牌填充速率(每秒)
     * @return true表示请求被允许，false表示被限流
     */
    public boolean isAllowed(String key, Integer capacity, Integer refillRate) {
        try {
            long now = System.currentTimeMillis();
            DefaultRedisScript<List> script = new DefaultRedisScript<>(TOKEN_BUCKET_LUA_SCRIPT, List.class);
            
            List result = Objects.requireNonNull(
                redisTemplate.execute(
                    script,
                    Arrays.asList(key),
                    String.valueOf(now),
                    String.valueOf(capacity),
                    String.valueOf(refillRate)
                )
            );

            if (result != null && result.size() >= 1) {
                Long allowed = (Long) result.get(0);
                Long remainingTokens = result.size() > 1 ? (Long) result.get(1) : 0L;

                if (allowed == 1L) {
                    log.debug("限流检查通过: key={}, 剩余令牌数={}", key, remainingTokens);
                    return true;
                } else {
                    log.warn("请求被限流: key={}, 剩余令牌数={}", key, remainingTokens);
                    return false;
                }
            }
        } catch (Exception e) {
            log.error("限流器执行出错: key={}", key, e);
            // 降级处理：执行异常时允许请求通过
            return true;
        }

        return false;
    }

    /**
     * 获取限流器状态信息（用于监控）
     * @param key 限流key
     * @return 包含当前令牌数和上次填充时间的信息
     */
    public String getStatus(String key) {
        try {
            String tokens = redisTemplate.opsForHash().get(key, "tokens").toString();
            String lastRefillTime = redisTemplate.opsForHash().get(key, "last_refill_time").toString();
            return String.format("tokens=%s, lastRefillTime=%s", tokens, lastRefillTime);
        } catch (Exception e) {
            log.error("获取限流器状态出错: key={}", key, e);
            return "unknown";
        }
    }

    /**
     * 重置限流器
     * @param key 限流key
     * @param capacity 令牌桶容量
     */
    public void reset(String key, Integer capacity) {
        try {
            redisTemplate.opsForHash().put(key, "tokens", String.valueOf(capacity));
            redisTemplate.opsForHash().put(key, "last_refill_time", String.valueOf(System.currentTimeMillis()));
            redisTemplate.expire(key, java.time.Duration.ofDays(1));
            log.info("已重置限流器: key={}, capacity={}", key, capacity);
        } catch (Exception e) {
            log.error("重置限流器失败: key={}", key, e);
        }
    }
}

package com.hcsy.gateway.utils;

import java.time.Duration;
import java.util.List;

import org.springframework.data.redis.core.ReactiveStringRedisTemplate;
import org.springframework.data.redis.core.script.RedisScript;
import org.springframework.stereotype.Component;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import reactor.core.publisher.Mono;

/**
 * Redis 响应式令牌桶限流器。
 */
@Component
@Slf4j
@RequiredArgsConstructor
public class TokenBucketRateLimiter {

    @SuppressWarnings("rawtypes")
    private static final RedisScript<List> TOKEN_BUCKET_SCRIPT = RedisScript.of(
            "local bucket_key = KEYS[1]\n"
                    + "local now = tonumber(ARGV[1])\n"
                    + "local capacity = tonumber(ARGV[2])\n"
                    + "local refill_rate = tonumber(ARGV[3])\n"
                    + "local last_refill_time = redis.call('HGET', bucket_key, 'last_refill_time')\n"
                    + "local current_tokens = redis.call('HGET', bucket_key, 'tokens')\n"
                    + "if not last_refill_time then\n"
                    + "    redis.call('HSET', bucket_key, 'last_refill_time', now)\n"
                    + "    redis.call('HSET', bucket_key, 'tokens', capacity - 1)\n"
                    + "    redis.call('EXPIRE', bucket_key, 86400)\n"
                    + "    return {1, capacity - 1}\n"
                    + "end\n"
                    + "last_refill_time = tonumber(last_refill_time)\n"
                    + "current_tokens = tonumber(current_tokens)\n"
                    + "local time_passed = math.max(0, (now - last_refill_time) / 1000)\n"
                    + "local tokens_to_add = math.floor(time_passed * refill_rate)\n"
                    + "local new_tokens = math.min(capacity, current_tokens + tokens_to_add)\n"
                    + "redis.call('HSET', bucket_key, 'last_refill_time', now)\n"
                    + "if new_tokens >= 1 then\n"
                    + "    new_tokens = new_tokens - 1\n"
                    + "    redis.call('HSET', bucket_key, 'tokens', new_tokens)\n"
                    + "    redis.call('EXPIRE', bucket_key, 86400)\n"
                    + "    return {1, new_tokens}\n"
                    + "end\n"
                    + "redis.call('HSET', bucket_key, 'tokens', new_tokens)\n"
                    + "redis.call('EXPIRE', bucket_key, 86400)\n"
                    + "return {0, new_tokens}\n",
            List.class);

    private static final RedisScript<Long> RESET_SCRIPT = RedisScript.of(
            "redis.call('HSET', KEYS[1], 'tokens', ARGV[1])\n"
                    + "redis.call('HSET', KEYS[1], 'last_refill_time', ARGV[2])\n"
                    + "redis.call('EXPIRE', KEYS[1], ARGV[3])\n"
                    + "return 1\n",
            Long.class);

    private final ReactiveStringRedisTemplate redisTemplate;

    @SuppressWarnings("null")
    public Mono<Boolean> isAllowed(String key, Integer capacity, Integer refillRate) {
        List<String> args = List.of(
                String.valueOf(System.currentTimeMillis()),
                String.valueOf(capacity),
                String.valueOf(refillRate));
        return redisTemplate.execute(TOKEN_BUCKET_SCRIPT, List.of(key), args)
                .next()
                .map(result -> isAllowedResult(result, key))
                .defaultIfEmpty(false)
                .onErrorResume(error -> {
                    log.error("限流器执行出错: key={}, Redis异常，拒绝请求", key, error);
                    return Mono.just(false);
                });
    }

    @SuppressWarnings("null")
    public Mono<String> getStatus(String key) {
        Mono<String> tokens = redisTemplate.<String, String>opsForHash()
                .get(key, "tokens")
                .defaultIfEmpty("unknown");
        Mono<String> lastRefillTime = redisTemplate.<String, String>opsForHash()
                .get(key, "last_refill_time")
                .defaultIfEmpty("unknown");
        return Mono.zip(tokens, lastRefillTime)
                .map(result -> String.format("tokens=%s, lastRefillTime=%s", result.getT1(), result.getT2()))
                .onErrorResume(error -> {
                    log.error("获取限流器状态出错: key={}", key, error);
                    return Mono.just("unknown");
                });
    }

    @SuppressWarnings("null")
    public Mono<Boolean> reset(String key, Integer capacity) {
        List<String> args = List.of(
                String.valueOf(capacity),
                String.valueOf(System.currentTimeMillis()),
                String.valueOf(Duration.ofDays(1).toSeconds()));
        return redisTemplate.execute(RESET_SCRIPT, List.of(key), args)
                .next()
                .map(result -> result == 1L)
                .defaultIfEmpty(false)
                .doOnSuccess(ignored -> log.info("已重置限流器: key={}, capacity={}", key, capacity))
                .onErrorResume(error -> {
                    log.error("重置限流器失败: key={}", key, error);
                    return Mono.just(false);
                });
    }

    private boolean isAllowedResult(List<?> result, String key) {
        if (result.isEmpty()) {
            return false;
        }

        long allowed = ((Number) result.get(0)).longValue();
        long remainingTokens = result.size() > 1 ? ((Number) result.get(1)).longValue() : 0L;
        if (allowed == 1L) {
            log.debug("限流检查通过: key={}, 剩余令牌数={}", key, remainingTokens);
            return true;
        }

        log.warn("请求被限流: key={}, 剩余令牌数={}", key, remainingTokens);
        return false;
    }
}

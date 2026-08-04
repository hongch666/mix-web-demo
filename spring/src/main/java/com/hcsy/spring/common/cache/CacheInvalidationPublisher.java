package com.hcsy.spring.common.cache;

import org.springframework.data.redis.core.ReactiveStringRedisTemplate;
import org.springframework.stereotype.Component;

import com.hcsy.spring.common.constants.Messages;
import com.hcsy.spring.common.constants.RedisKeys;
import com.hcsy.spring.common.utils.SimpleLogger;

import lombok.RequiredArgsConstructor;
import reactor.core.publisher.Mono;

/**
 * 通过 Redis 广播多实例本地缓存失效事件。
 */
@Component
@RequiredArgsConstructor
public class CacheInvalidationPublisher {
    private static final String INVALIDATION_MESSAGE = "evict";

    private final ReactiveStringRedisTemplate redisTemplate;
    private final SimpleLogger logger;

    public Mono<Void> publishCategoryEviction() {
        return publish(RedisKeys.categoryCacheInvalidationChannel());
    }

    public Mono<Void> publishUserEviction() {
        return publish(RedisKeys.userCacheInvalidationChannel());
    }

    @SuppressWarnings("null")
    private Mono<Void> publish(String channel) {
        return redisTemplate.convertAndSend(channel, INVALIDATION_MESSAGE)
            .onErrorResume(error -> {
                logger.error(Messages.CACHE_INVALIDATION_PUBLISH_FAILED, channel, error.getMessage(), error);
                return Mono.just(0L);
            })
            .then();
    }
}

package com.hcsy.spring.common.cache;

import org.springframework.data.redis.listener.ChannelTopic;
import org.springframework.data.redis.listener.ReactiveRedisMessageListenerContainer;
import org.springframework.stereotype.Component;

import com.hcsy.spring.common.constants.Messages;
import com.hcsy.spring.common.constants.RedisKeys;
import com.hcsy.spring.common.utils.SimpleLogger;

import jakarta.annotation.PostConstruct;
import jakarta.annotation.PreDestroy;
import lombok.RequiredArgsConstructor;
import reactor.core.Disposable;

/**
 * 接收 Redis 失效消息并清理当前实例的 Caffeine 缓存。
 */
@Component
@RequiredArgsConstructor
public class LocalCacheInvalidationSubscriber {
    private final ReactiveRedisMessageListenerContainer listenerContainer;
    private final CategoryLocalCache categoryLocalCache;
    private final UserLocalCache userLocalCache;
    private final SimpleLogger logger;

    private Disposable categorySubscription;
    private Disposable userSubscription;

    @SuppressWarnings("null")
    @PostConstruct
    void subscribe() {
        String categoryChannel = RedisKeys.categoryCacheInvalidationChannel();
        categorySubscription = listenerContainer.receive(ChannelTopic.of(categoryChannel))
            .subscribe(message -> categoryLocalCache.evictAll(),
                error -> logger.error(Messages.CACHE_INVALIDATION_SUBSCRIBE_FAILED,
                    categoryChannel, error.getMessage(), error));

        String userChannel = RedisKeys.userCacheInvalidationChannel();
        userSubscription = listenerContainer.receive(ChannelTopic.of(userChannel))
            .subscribe(message -> userLocalCache.evictAll(),
                error -> logger.error(Messages.CACHE_INVALIDATION_SUBSCRIBE_FAILED,
                    userChannel, error.getMessage(), error));
    }

    @PreDestroy
    void dispose() {
        if (categorySubscription != null) {
            categorySubscription.dispose();
        }
        if (userSubscription != null) {
            userSubscription.dispose();
        }
    }
}

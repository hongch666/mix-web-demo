package com.hcsy.spring.common.utils;

import java.util.Map;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.TimeUnit;
import java.util.function.Supplier;
import java.util.function.ToLongFunction;

import org.springframework.data.redis.listener.ChannelTopic;
import org.springframework.data.redis.listener.ReactiveRedisMessageListenerContainer;
import org.springframework.stereotype.Component;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.github.benmanes.caffeine.cache.AsyncCache;
import com.github.benmanes.caffeine.cache.Caffeine;
import com.github.benmanes.caffeine.cache.Expiry;
import com.hcsy.spring.common.constants.Messages;
import jakarta.annotation.PreDestroy;
import lombok.RequiredArgsConstructor;
import reactor.core.Disposable;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

/**
 * 通用响应式多级缓存工具，统一管理 Caffeine、Redis 与多实例失效通知。
 */
@Component
@RequiredArgsConstructor
public class CacheUtil {
    private static final String INVALIDATION_MESSAGE = "evict";

    private final RedisUtil redisUtil;
    private final ObjectMapper objectMapper;
    private final ReactiveRedisMessageListenerContainer listenerContainer;
    private final SimpleLogger logger;

    private final Map<String, AsyncCache<Object, Object>> localCaches = new ConcurrentHashMap<>();
    private final Map<String, Set<String>> cacheNamesByChannel = new ConcurrentHashMap<>();
    private final Map<String, Disposable> subscriptions = new ConcurrentHashMap<>();

    public <K, V> Mono<V> get(
        CacheOptions<V> options,
        K localKey,
        String redisKey,
        Class<V> valueType,
        Supplier<Mono<V>> loader) {
        return getFromLocal(options, localKey,
            () -> loadFromRedisOrSource(redisKey, valueType, loader, options.ttlResolver()));
    }

    public <K, V> Mono<V> get(
        CacheOptions<V> options,
        K localKey,
        String redisKey,
        TypeReference<V> valueType,
        Supplier<Mono<V>> loader) {
        return getFromLocal(options, localKey,
            () -> loadFromRedisOrSource(redisKey, valueType, loader, options.ttlResolver()));
    }

    public Mono<Void> evict(String redisKey, CacheOptions<?>... options) {
        return Mono.fromRunnable(() -> evictLocal(options))
            .then(redisUtil.delete(redisKey))
            .onErrorResume(error -> {
                logger.error(Messages.CACHE_L2_CLEAR_FAILED, error.getMessage(), error);
                return Mono.just(false);
            })
            .then(publishInvalidation(options));
    }

    public Mono<Void> evictAll(String redisPattern, CacheOptions<?>... options) {
        return Mono.fromRunnable(() -> evictLocal(options))
            .then(redisUtil.getKeys(redisPattern).collectList())
            .flatMap(keys -> keys.isEmpty() ? Mono.empty() : redisUtil.delete(keys).then())
            .onErrorResume(error -> {
                logger.error(Messages.CACHE_L2_CLEAR_FAILED, error.getMessage(), error);
                return Mono.empty();
            })
            .then(publishInvalidation(options));
    }

    @SuppressWarnings("null")
    @PreDestroy
    void dispose() {
        subscriptions.values().forEach(Disposable::dispose);
        subscriptions.clear();
    }

    private <K, V> Mono<V> getFromLocal(
        CacheOptions<V> options,
        K localKey,
        Supplier<Mono<V>> loader) {
        register(options);
        AsyncCache<Object, Object> localCache = localCaches.computeIfAbsent(options.name(),
            ignored -> createLocalCache(options));
        return Mono.defer(() -> Mono.fromFuture(localCache.get(localKey,
            (ignoredKey, executor) -> loader.get().toFuture())).map(value -> cast(value)));
    }

    private AsyncCache<Object, Object> createLocalCache(CacheOptions<?> options) {
        return Caffeine.newBuilder()
            .maximumSize(options.maximumSize())
            .expireAfter(new CacheExpiry(options))
            .recordStats()
            .buildAsync();
    }

    private void register(CacheOptions<?> options) {
        cacheNamesByChannel.computeIfAbsent(options.invalidationChannel(), ignored -> ConcurrentHashMap.newKeySet())
            .add(options.name());
        subscriptions.computeIfAbsent(options.invalidationChannel(), this::subscribe);
    }

    @SuppressWarnings("null")
    private Disposable subscribe(String channel) {
        return listenerContainer.receive(ChannelTopic.of(channel))
            .subscribe(message -> evictLocalByChannel(channel),
                error -> logger.error(Messages.CACHE_INVALIDATION_SUBSCRIBE_FAILED,
                    channel, error.getMessage(), error));
    }

    private void evictLocal(CacheOptions<?>... options) {
        for (CacheOptions<?> option : options) {
            AsyncCache<Object, Object> localCache = localCaches.get(option.name());
            if (localCache != null) {
                localCache.synchronous().invalidateAll();
            }
        }
    }

    private void evictLocalByChannel(String channel) {
        cacheNamesByChannel.getOrDefault(channel, Set.of()).forEach(cacheName -> {
            AsyncCache<Object, Object> localCache = localCaches.get(cacheName);
            if (localCache != null) {
                localCache.synchronous().invalidateAll();
            }
        });
    }

    @SuppressWarnings("null")
    private Mono<Void> publishInvalidation(CacheOptions<?>... options) {
        return Flux.fromArray(options)
            .map(CacheOptions::invalidationChannel)
            .distinct()
            .flatMap(this::publish)
            .then();
    }

    private Mono<Void> publish(String channel) {
        return redisUtil.publish(channel, INVALIDATION_MESSAGE)
            .onErrorResume(error -> {
                logger.error(Messages.CACHE_INVALIDATION_PUBLISH_FAILED, channel, error.getMessage(), error);
                return Mono.just(0L);
            })
            .then();
    }

    private <V> Mono<V> loadFromRedisOrSource(
        String redisKey,
        Class<V> valueType,
        Supplier<Mono<V>> loader,
        ToLongFunction<V> ttlResolver) {
        return redisUtil.get(redisKey)
            .flatMap(json -> deserialize(json, valueType, redisKey))
            .onErrorResume(error -> cacheReadFallback(redisKey, error))
            .switchIfEmpty(Mono.defer(() -> loader.get()
                .flatMap(value -> writeToRedis(redisKey, value, ttlResolver.applyAsLong(value))
                    .thenReturn(value))));
    }

    private <V> Mono<V> loadFromRedisOrSource(
        String redisKey,
        TypeReference<V> valueType,
        Supplier<Mono<V>> loader,
        ToLongFunction<V> ttlResolver) {
        return redisUtil.get(redisKey)
            .flatMap(json -> deserialize(json, valueType, redisKey))
            .onErrorResume(error -> cacheReadFallback(redisKey, error))
            .switchIfEmpty(Mono.defer(() -> loader.get()
                .flatMap(value -> writeToRedis(redisKey, value, ttlResolver.applyAsLong(value))
                    .thenReturn(value))));
    }

    private <V> Mono<V> deserialize(String json, Class<V> valueType, String redisKey) {
        return Mono.fromCallable(() -> objectMapper.readValue(json, valueType))
            .onErrorResume(error -> clearInvalidRedisValue(redisKey, error));
    }

    private <V> Mono<V> deserialize(String json, TypeReference<V> valueType, String redisKey) {
        return Mono.fromCallable(() -> objectMapper.readValue(json, valueType))
            .onErrorResume(error -> clearInvalidRedisValue(redisKey, error));
    }

    private <V> Mono<V> clearInvalidRedisValue(String redisKey, Throwable error) {
        logger.error(Messages.CACHE_DESERIALIZE_FAILED, redisKey, error.getMessage(), error);
        return redisUtil.delete(redisKey).then(Mono.empty());
    }

    private <V> Mono<V> cacheReadFallback(String redisKey, Throwable error) {
        logger.error(Messages.CACHE_READ_FAILED, redisKey, error.getMessage(), error);
        return Mono.empty();
    }

    private Mono<Void> writeToRedis(String redisKey, Object value, long ttlSeconds) {
        return Mono.fromCallable(() -> objectMapper.writeValueAsString(value))
            .flatMap(json -> redisUtil.set(redisKey, json, ttlSeconds))
            .onErrorResume(error -> {
                logger.error(Messages.CACHE_WRITE_FAILED, redisKey, error.getMessage(), error);
                return Mono.just(false);
            })
            .then();
    }

    @SuppressWarnings("unchecked")
    private <V> V cast(Object value) {
        return (V) value;
    }

    public record CacheOptions<V>(
        String name,
        String invalidationChannel,
        long maximumSize,
        ToLongFunction<V> ttlResolver) {

        public CacheOptions {
            if (name == null || name.isBlank()) {
                throw new IllegalArgumentException("缓存名称不能为空");
            }
            if (invalidationChannel == null || invalidationChannel.isBlank()) {
                throw new IllegalArgumentException("缓存失效频道不能为空");
            }
            if (maximumSize < 1) {
                throw new IllegalArgumentException("缓存容量必须大于零");
            }
            if (ttlResolver == null) {
                throw new IllegalArgumentException("缓存过期时间不能为空");
            }
        }

        public static <V> CacheOptions<V> fixed(
            String name,
            String invalidationChannel,
            long maximumSize,
            long ttlSeconds) {
            return new CacheOptions<>(name, invalidationChannel, maximumSize, value -> ttlSeconds);
        }
    }

    private static final class CacheExpiry implements Expiry<Object, Object> {
        private final CacheOptions<?> options;

        private CacheExpiry(CacheOptions<?> options) {
            this.options = options;
        }

        @Override
        public long expireAfterCreate(Object key, Object value, long currentTime) {
            return TimeUnit.SECONDS.toNanos(Math.max(1L, resolveTtl(value)));
        }

        @Override
        public long expireAfterUpdate(Object key, Object value, long currentTime, long currentDuration) {
            return currentDuration;
        }

        @Override
        public long expireAfterRead(Object key, Object value, long currentTime, long currentDuration) {
            return currentDuration;
        }

        @SuppressWarnings("unchecked")
        private long resolveTtl(Object value) {
            return ((ToLongFunction<Object>) options.ttlResolver()).applyAsLong(value);
        }
    }
}

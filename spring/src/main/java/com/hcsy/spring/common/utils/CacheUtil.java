package com.hcsy.spring.common.utils;

import java.util.Map;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.TimeUnit;
import java.util.function.Supplier;

import org.springframework.data.redis.listener.ChannelTopic;
import org.springframework.data.redis.listener.ReactiveRedisMessageListenerContainer;
import org.springframework.stereotype.Component;

import com.hcsy.spring.common.constants.Defaults;
import com.hcsy.spring.common.constants.Messages;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.github.benmanes.caffeine.cache.AsyncCache;
import com.github.benmanes.caffeine.cache.Caffeine;
import jakarta.annotation.PreDestroy;
import lombok.RequiredArgsConstructor;
import reactor.core.Disposable;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;
import reactor.core.scheduler.Schedulers;

/**
 * 通用响应式多级缓存工具，统一管理 Caffeine、Redis 与多实例失效通知
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

    /**
     * 按缓存选项先查本地缓存再回源 Redis 或加载器（Class 类型）
     */
    public <K, V> Mono<V> get(
        CacheOptions<V> options,
        K localKey,
        String redisKey,
        Class<V> valueType,
        Supplier<Mono<V>> loader) {
        return getFromLocal(options, localKey,
            () -> loadFromRedisOrSource(redisKey, valueType, loader, options.l2TtlSeconds()));
    }

    /**
     * 按缓存选项先查本地缓存再回源 Redis 或加载器（TypeReference 复杂类型）
     */
    public <K, V> Mono<V> get(
        CacheOptions<V> options,
        K localKey,
        String redisKey,
        TypeReference<V> valueType,
        Supplier<Mono<V>> loader) {
        return getFromLocal(options, localKey,
            () -> loadFromRedisOrSource(redisKey, valueType, loader, options.l2TtlSeconds()));
    }

    /**
     * 删除指定 Redis key 并失效本地缓存、广播失效通知
     */
    public Mono<Void> evict(String redisKey, CacheOptions<?>... options) {
        return evictLocal(options)
            .then(redisUtil.delete(redisKey))
            .onErrorResume(error -> {
                logger.error(Messages.CACHE_L2_CLEAR_FAILED, error.getMessage(), error);
                return Mono.just(false);
            })
            .then(publishInvalidation(options));
    }

    /**
     * 按 pattern 批量删除 Redis key 并失效本地缓存、广播失效通知
     */
    public Mono<Void> evictAll(String redisPattern, CacheOptions<?>... options) {
        return evictLocal(options)
            .then(redisUtil.getKeys(redisPattern).collectList())
            .flatMap(keys -> keys.isEmpty() ? Mono.empty() : redisUtil.delete(keys).then())
            .onErrorResume(error -> {
                logger.error(Messages.CACHE_L2_CLEAR_FAILED, error.getMessage(), error);
                return Mono.empty();
            })
            .then(publishInvalidation(options));
    }

    /**
     * 容器销毁时释放所有缓存失效订阅
     */
    @PreDestroy
    void dispose() {
        subscriptions.values().forEach(Disposable::dispose);
        subscriptions.clear();
    }

    /**
     * 从 Caffeine 本地缓存读取，未命中时执行加载器回源
     */
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

    /**
     * 按缓存选项创建带容量上限与 L1 过期时间的 Caffeine 异步缓存
     */
    private AsyncCache<Object, Object> createLocalCache(CacheOptions<?> options) {
        return Caffeine.newBuilder()
            .maximumSize(options.maximumSize())
            .expireAfterWrite(options.l1TtlSeconds(), TimeUnit.SECONDS)
            .recordStats()
            .buildAsync();
    }

    /**
     * 登记缓存名称与失效频道的映射并确保频道已订阅
     */
    private void register(CacheOptions<?> options) {
        cacheNamesByChannel.computeIfAbsent(options.invalidationChannel(), ignored -> ConcurrentHashMap.newKeySet())
            .add(options.name());
        subscriptions.computeIfAbsent(options.invalidationChannel(), this::subscribe);
    }

    /**
     * 订阅失效频道，收到消息后清空该频道关联的本地缓存
     */
    private Disposable subscribe(String channel) {
        return listenerContainer.receive(ChannelTopic.of(channel))
            .concatMap(ignoredMessage -> evictLocalByChannel(channel)
                .onErrorResume(error -> {
                    logger.error(Messages.CACHE_INVALIDATION_SUBSCRIBE_FAILED,
                        channel, error.getMessage(), error);
                    return Mono.empty();
                }))
            .subscribe(ignored -> {
            },
                error -> logger.error(Messages.CACHE_INVALIDATION_SUBSCRIBE_FAILED,
                    channel, error.getMessage(), error));
    }

    /**
     * 清空指定缓存选项对应的本地缓存
     */
    private Mono<Void> evictLocal(CacheOptions<?>... options) {
        return Mono.fromRunnable(() -> {
            for (CacheOptions<?> option : options) {
                AsyncCache<Object, Object> localCache = localCaches.get(option.name());
                if (localCache != null) {
                    localCache.synchronous().invalidateAll();
                }
            }
        })
            .subscribeOn(Schedulers.boundedElastic())
            .then();
    }

    /**
     * 按失效频道清空关联的全部本地缓存
     */
    private Mono<Void> evictLocalByChannel(String channel) {
        return Mono.fromRunnable(() -> {
            cacheNamesByChannel.getOrDefault(channel, Set.of()).forEach(cacheName -> {
                AsyncCache<Object, Object> localCache = localCaches.get(cacheName);
                if (localCache != null) {
                    localCache.synchronous().invalidateAll();
                }
            });
        })
            .subscribeOn(Schedulers.boundedElastic())
            .then();
    }

    /**
     * 向各缓存选项的失效频道发布本地缓存失效通知
     */
    private Mono<Void> publishInvalidation(CacheOptions<?>... options) {
        return Flux.fromArray(options)
            .map(CacheOptions::invalidationChannel)
            .distinct()
            .flatMap(this::publish)
            .then();
    }

    /**
     * 向指定 Redis 频道发布缓存失效消息
     */
    private Mono<Void> publish(String channel) {
        return redisUtil.publish(channel, INVALIDATION_MESSAGE)
            .onErrorResume(error -> {
                logger.error(Messages.CACHE_INVALIDATION_PUBLISH_FAILED, channel, error.getMessage(), error);
                return Mono.just(0L);
            })
            .then();
    }

    /**
     * 从 Redis 读取缓存值，未命中时执行加载器并写回（Class 类型）
     */
    private <V> Mono<V> loadFromRedisOrSource(
        String redisKey,
        Class<V> valueType,
        Supplier<Mono<V>> loader,
        long ttlSeconds) {
        return redisUtil.get(redisKey)
            .flatMap(json -> deserialize(json, valueType, redisKey))
            .onErrorResume(error -> cacheReadFallback(redisKey, error))
            .switchIfEmpty(Mono.defer(() -> loader.get()
                .flatMap(value -> writeToRedis(redisKey, value, ttlSeconds)
                    .thenReturn(value))));
    }

    /**
     * 从 Redis 读取缓存值，未命中时执行加载器并写回（TypeReference 类型）
     */
    private <V> Mono<V> loadFromRedisOrSource(
        String redisKey,
        TypeReference<V> valueType,
        Supplier<Mono<V>> loader,
        long ttlSeconds) {
        return redisUtil.get(redisKey)
            .flatMap(json -> deserialize(json, valueType, redisKey))
            .onErrorResume(error -> cacheReadFallback(redisKey, error))
            .switchIfEmpty(Mono.defer(() -> loader.get()
                .flatMap(value -> writeToRedis(redisKey, value, ttlSeconds)
                    .thenReturn(value))));
    }

    /**
     * 反序列化 Redis 缓存值，失败时清除无效缓存（Class 类型）
     */
    private <V> Mono<V> deserialize(String json, Class<V> valueType, String redisKey) {
        return Mono.fromCallable(() -> objectMapper.readValue(json, valueType))
            .onErrorResume(error -> clearInvalidRedisValue(redisKey, error));
    }

    /**
     * 反序列化 Redis 缓存值，失败时清除无效缓存（TypeReference 类型）
     */
    private <V> Mono<V> deserialize(String json, TypeReference<V> valueType, String redisKey) {
        return Mono.fromCallable(() -> objectMapper.readValue(json, valueType))
            .onErrorResume(error -> clearInvalidRedisValue(redisKey, error));
    }

    /**
     * 记录反序列化失败日志并删除无效的 Redis 缓存
     */
    private <V> Mono<V> clearInvalidRedisValue(String redisKey, Throwable error) {
        logger.error(Messages.CACHE_DESERIALIZE_FAILED, redisKey, error.getMessage(), error);
        return redisUtil.delete(redisKey).then(Mono.empty());
    }

    /**
     * Redis 缓存读取失败时记录日志并降级为直接回源加载
     */
    private <V> Mono<V> cacheReadFallback(String redisKey, Throwable error) {
        logger.error(Messages.CACHE_READ_FAILED, redisKey, error.getMessage(), error);
        return Mono.empty();
    }

    /**
     * 将值序列化后写入 Redis 二级缓存，失败时仅记录日志不中断业务
     */
    private Mono<Void> writeToRedis(String redisKey, Object value, long ttlSeconds) {
        return Mono.fromCallable(() -> objectMapper.writeValueAsString(value))
            .flatMap(json -> redisUtil.set(redisKey, json, ttlSeconds))
            .onErrorResume(error -> {
                logger.error(Messages.CACHE_WRITE_FAILED, redisKey, error.getMessage(), error);
                return Mono.just(false);
            })
            .then();
    }

    /**
     * 将本地缓存取出的对象强转为目标泛型类型
     */
    private <V> V cast(Object value) {
        return (V) value;
    }

    /**
     * 多级缓存选项，定义缓存名称、失效频道、容量上限与 L1/L2 TTL
     */
    public record CacheOptions<V>(
        String name,
        String invalidationChannel,
        long maximumSize,
        long l1TtlSeconds,
        long l2TtlSeconds) {

        public CacheOptions {
            if (name == null || name.isBlank()) {
                throw new IllegalArgumentException(Messages.CACHE_OPTIONS_NAME_NOT_BLANK);
            }
            if (invalidationChannel == null || invalidationChannel.isBlank()) {
                throw new IllegalArgumentException(Messages.CACHE_OPTIONS_CHANNEL_NOT_BLANK);
            }
            if (maximumSize < 1) {
                throw new IllegalArgumentException(Messages.CACHE_OPTIONS_MAXIMUM_SIZE_POSITIVE);
            }
            if (l1TtlSeconds < 1) {
                throw new IllegalArgumentException(Messages.CACHE_OPTIONS_L1_TTL_POSITIVE);
            }
            if (l2TtlSeconds < 1) {
                throw new IllegalArgumentException(Messages.CACHE_OPTIONS_L2_TTL_POSITIVE);
            }
        }

        // 全参版本：显式指定 L1/L2 TTL（特殊场景使用）
        public static <V> CacheOptions<V> fixed(
            String name,
            String invalidationChannel,
            long maximumSize,
            long l1TtlSeconds,
            long l2TtlSeconds) {
            return new CacheOptions<>(name, invalidationChannel, maximumSize, l1TtlSeconds, l2TtlSeconds);
        }

        // 简化版本：自动使用全局统一 TTL（L1=5min / L2=24h），业务方无需再引用 Defaults 或自行定义 TTL 中转常量
        public static <V> CacheOptions<V> fixed(
            String name,
            String invalidationChannel,
            long maximumSize) {
            return new CacheOptions<>(name, invalidationChannel, maximumSize,
                Defaults.CACHE_L1_TTL_SECONDS, Defaults.CACHE_L2_TTL_SECONDS);
        }
    }
}

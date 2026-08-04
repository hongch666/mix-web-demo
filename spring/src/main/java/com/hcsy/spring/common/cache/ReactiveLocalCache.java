package com.hcsy.spring.common.cache;

import java.util.function.Supplier;

import org.springframework.stereotype.Component;

import com.github.benmanes.caffeine.cache.AsyncCache;

import reactor.core.publisher.Mono;

/**
 * Caffeine 异步缓存与 Reactor 的桥接工具。
 */
@Component
public class ReactiveLocalCache {

    public <K, V> Mono<V> get(AsyncCache<K, V> cache, K key, Supplier<Mono<V>> loader) {
        return Mono.defer(() -> Mono.fromFuture(cache.get(key,
            (ignoredKey, executor) -> loader.get().toFuture())));
    }
}

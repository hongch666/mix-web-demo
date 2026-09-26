package com.hcsy.spring.common.utils;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.data.redis.listener.ChannelTopic;
import org.springframework.data.redis.listener.ReactiveRedisMessageListenerContainer;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

import com.fasterxml.jackson.databind.ObjectMapper;
import reactor.core.publisher.Mono;
import reactor.test.StepVerifier;

class CacheUtilTest {
    // 验证该场景的预期行为
    @Test
    @DisplayName("缓存选项拒绝无效参数")
    void rejectsInvalidOptions() {
        assertThrows(IllegalArgumentException.class, () -> new CacheUtil.CacheOptions<>("", "channel", 1, 1, 1));
        assertThrows(IllegalArgumentException.class, () -> new CacheUtil.CacheOptions<>("name", "channel", 0, 1, 1));
    }

    // 验证该场景的预期行为

    @Test
    @DisplayName("缓存未命中时加载源数据并写入本地缓存")
    void loadsSourceOnMiss() {
        RedisUtil redis = mock(RedisUtil.class);
        ReactiveRedisMessageListenerContainer listener = mock(ReactiveRedisMessageListenerContainer.class);
        when(listener.receive(org.mockito.ArgumentMatchers.any(ChannelTopic[].class)))
            .thenReturn(reactor.core.publisher.Flux.empty());
        when(redis.get("k")).thenReturn(Mono.empty());
        when(redis.set("k", "\"v\"", 10)).thenReturn(Mono.just(true));
        CacheUtil util = new CacheUtil(redis, new ObjectMapper(), listener,
            mock(SimpleLogger.class));
        var options = CacheUtil.CacheOptions.<String>fixed("test", "channel", 10, 60, 10);
        StepVerifier.create(util.get(options, "local", "k", String.class, () -> Mono.just("v")))
            .expectNext("v").verifyComplete();
        assertEquals("test", options.name());
    }
}

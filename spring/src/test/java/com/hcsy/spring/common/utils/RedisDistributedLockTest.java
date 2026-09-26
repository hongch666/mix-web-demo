package com.hcsy.spring.common.utils;

import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.data.redis.core.ReactiveStringRedisTemplate;

import reactor.core.publisher.Flux;
import reactor.test.StepVerifier;

class RedisDistributedLockTest {
    // 验证该场景的预期行为
    @Test
    @DisplayName("获取锁失败时返回空结果")
    void returnsEmptyWhenLockBusy() {
        ReactiveStringRedisTemplate template = mock(ReactiveStringRedisTemplate.class);
        var ops = mock(org.springframework.data.redis.core.ReactiveValueOperations.class);
        when(template.opsForValue()).thenReturn(ops);
        when(ops.setIfAbsent(org.mockito.ArgumentMatchers.anyString(), org.mockito.ArgumentMatchers.anyString(),
            org.mockito.ArgumentMatchers.any())).thenReturn(reactor.core.publisher.Mono.just(false));
        StepVerifier.create(new RedisDistributedLock(template).tryLock("k", 10)).verifyComplete();
    }

    // 验证该场景的预期行为

    @Test
    @DisplayName("解锁脚本无结果时返回 false")
    void unlockDefaultsFalse() {
        ReactiveStringRedisTemplate template = mock(ReactiveStringRedisTemplate.class);
        when(template.execute(org.mockito.ArgumentMatchers.any(), org.mockito.ArgumentMatchers.anyList(),
            org.mockito.ArgumentMatchers.anyList())).thenReturn(Flux.empty());
        StepVerifier.create(new RedisDistributedLock(template).unlock("k", "v")).expectNext(false).verifyComplete();
    }
}

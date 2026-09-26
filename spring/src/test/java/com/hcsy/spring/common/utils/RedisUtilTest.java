package com.hcsy.spring.common.utils;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.data.redis.core.ReactiveStringRedisTemplate;

import reactor.core.publisher.Mono;
import reactor.test.StepVerifier;

class RedisUtilTest {
    // 验证该场景的预期行为
    @Test
    @DisplayName("空键列表直接返回空结果")
    void batchGetEmpty() {
        RedisUtil util = new RedisUtil(mock(ReactiveStringRedisTemplate.class));
        StepVerifier.create(util.batchGet(java.util.List.of())).assertNext(values -> assertEquals(0, values.size()))
            .verifyComplete();
    }

    // 验证该场景的预期行为

    @Test
    @DisplayName("删除键将 Redis 数量转换为布尔结果")
    void deleteMapsCount() {
        ReactiveStringRedisTemplate template = mock(ReactiveStringRedisTemplate.class);
        when(template.delete("k")).thenReturn(Mono.just(1L));
        RedisUtil util = new RedisUtil(template);
        StepVerifier.create(util.delete("k")).expectNext(true).verifyComplete();
    }
}

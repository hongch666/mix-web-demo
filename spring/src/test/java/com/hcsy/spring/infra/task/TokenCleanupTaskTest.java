package com.hcsy.spring.infra.task;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import com.hcsy.spring.api.service.TokenService;
import com.hcsy.spring.common.utils.RedisDistributedLock;
import com.hcsy.spring.common.utils.SimpleLogger;

import static org.mockito.Mockito.*;

import reactor.core.publisher.Mono;
import reactor.test.StepVerifier;

class TokenCleanupTaskTest {
    // 验证该场景的预期行为
    @Test
    @DisplayName("获取任务锁后执行清理并释放锁")
    void cleansAndReleasesLock() {
        TokenService service = mock(TokenService.class);
        RedisDistributedLock lock = mock(RedisDistributedLock.class);
        when(lock.tryLock(anyString(), anyLong())).thenReturn(Mono.just("lock"));
        when(service.cleanupExpiredTokens()).thenReturn(Mono.empty());
        when(lock.unlock(anyString(), eq("lock"))).thenReturn(Mono.just(true));
        StepVerifier.create(new TokenCleanupTask(service, mock(SimpleLogger.class), lock).cleanupExpiredTokens())
            .verifyComplete();
        verify(service).cleanupExpiredTokens();
        verify(lock).unlock(anyString(), eq("lock"));
    }
}

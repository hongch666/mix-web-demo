package com.hcsy.spring.application.task;

import static org.mockito.ArgumentMatchers.anyLong;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import com.hcsy.spring.application.service.TokenService;
import com.hcsy.spring.common.utils.RedisDistributedLock;
import com.hcsy.spring.common.utils.SimpleLogger;

import reactor.core.publisher.Mono;
import reactor.test.StepVerifier;

class TokenCleanupTaskTest {
    @Test
    @DisplayName("手动触发任务会在任务组件内订阅清理链")
    void triggerCleanupSubscribesToCleanup() {
        TokenService service = mock(TokenService.class);
        RedisDistributedLock lock = mock(RedisDistributedLock.class);
        when(lock.tryLock(anyString(), anyLong())).thenReturn(Mono.just("lock"));
        when(service.cleanupExpiredTokens()).thenReturn(Mono.empty());
        when(lock.unlock(anyString(), eq("lock"))).thenReturn(Mono.just(true));

        new TokenCleanupTask(service, mock(SimpleLogger.class), lock,
            mock(com.hcsy.spring.observability.MetricsRecorder.class)).triggerCleanup();

        verify(service).cleanupExpiredTokens();
        verify(lock).unlock(anyString(), eq("lock"));
    }

    // 验证该场景的预期行为
    @Test
    @DisplayName("获取任务锁后执行清理并释放锁")
    void cleansAndReleasesLock() {
        TokenService service = mock(TokenService.class);
        RedisDistributedLock lock = mock(RedisDistributedLock.class);
        when(lock.tryLock(anyString(), anyLong())).thenReturn(Mono.just("lock"));
        when(service.cleanupExpiredTokens()).thenReturn(Mono.empty());
        when(lock.unlock(anyString(), eq("lock"))).thenReturn(Mono.just(true));
        StepVerifier.create(new TokenCleanupTask(service, mock(SimpleLogger.class), lock,
            mock(com.hcsy.spring.observability.MetricsRecorder.class)).cleanupExpiredTokens())
            .verifyComplete();
        verify(service).cleanupExpiredTokens();
        verify(lock).unlock(anyString(), eq("lock"));
    }
}

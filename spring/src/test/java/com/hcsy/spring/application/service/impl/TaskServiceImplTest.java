package com.hcsy.spring.application.service.impl;

import static org.mockito.ArgumentMatchers.anyLong;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import com.hcsy.spring.application.service.TokenService;
import com.hcsy.spring.application.task.TokenCleanupTask;
import com.hcsy.spring.common.utils.RedisDistributedLock;
import com.hcsy.spring.common.utils.SimpleLogger;

import reactor.core.publisher.Mono;
import reactor.test.StepVerifier;

class TaskServiceImplTest {
    @Test
    @DisplayName("手动触发在后台订阅清理链并立即返回")
    void triggerTokenCleanupRunsCleanupInBackground() {
        TokenService service = mock(TokenService.class);
        RedisDistributedLock lock = mock(RedisDistributedLock.class);
        when(lock.tryLock(anyString(), anyLong())).thenReturn(Mono.just("lock"));
        when(service.cleanupExpiredTokens()).thenReturn(Mono.empty());
        when(lock.unlock(anyString(), eq("lock"))).thenReturn(Mono.just(true));

        TaskServiceImpl taskService = new TaskServiceImpl(
            new TokenCleanupTask(service, mock(SimpleLogger.class), lock,
                mock(com.hcsy.spring.observability.MetricsRecorder.class)),
            mock(SimpleLogger.class));

        StepVerifier.create(taskService.triggerTokenCleanup())
            .verifyComplete();

        verify(service).cleanupExpiredTokens();
        verify(lock).unlock(anyString(), eq("lock"));
    }
}

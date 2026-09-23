package com.hcsy.spring.core.aspect;

import org.aspectj.lang.ProceedingJoinPoint;
import org.aspectj.lang.reflect.MethodSignature;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import com.hcsy.spring.api.service.AsyncSyncService;
import com.hcsy.spring.common.constants.HttpCode;
import com.hcsy.spring.common.utils.Result;
import com.hcsy.spring.common.utils.UserContext;
import com.hcsy.spring.core.annotation.DataSync;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.lenient;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import reactor.core.publisher.Mono;
import reactor.test.StepVerifier;
import reactor.util.context.Context;

@ExtendWith(MockitoExtension.class)
class DataSyncAspectTest {

    @Mock
    private AsyncSyncService asyncSyncService;

    private DataSyncAspect aspect;

    @BeforeEach
    void setUp() {
        aspect = new DataSyncAspect(asyncSyncService);
        lenient().when(asyncSyncService.syncNeo4jAsync(anyString(), anyString()))
            .thenReturn(Mono.empty());
        lenient().when(asyncSyncService.syncWarehouseAsync(any(), any()))
            .thenReturn(Mono.empty());
    }

    @Test
    @DisplayName("业务成功时同时触发图谱与数仓同步")
    void triggersBothSyncsOnBusinessSuccess() throws Throwable {
        Mono<?> result = invoke(Mono.just(Result.success()));

        StepVerifier.create(result).expectNextCount(1).verifyComplete();

        verify(asyncSyncService).syncNeo4jAsync(anyString(), anyString());
        verify(asyncSyncService).syncWarehouseAsync(any(), any());
    }

    @Test
    @DisplayName("业务失败时不触发图谱与数仓同步")
    void skipsBothSyncsOnBusinessFailure() throws Throwable {
        Mono<?> result = invoke(Mono.just(Result.error(HttpCode.CONFLICT, "冲突")));

        StepVerifier.create(result).expectNextCount(1).verifyComplete();

        verify(asyncSyncService, never()).syncNeo4jAsync(anyString(), anyString());
        verify(asyncSyncService, never()).syncWarehouseAsync(any(), any());
    }

    @Test
    @DisplayName("业务错误码为 404 时同样不触发同步")
    void skipsSyncsOnNotFound() throws Throwable {
        Mono<?> result = invoke(Mono.just(Result.error(HttpCode.NOT_FOUND, "不存在")));

        StepVerifier.create(result).expectNextCount(1).verifyComplete();

        verify(asyncSyncService, never()).syncNeo4jAsync(anyString(), anyString());
        verify(asyncSyncService, never()).syncWarehouseAsync(any(), any());
    }

    @Test
    @DisplayName("主流程异常时不触发同步")
    void skipsSyncsOnUpstreamError() throws Throwable {
        Mono<?> result = invoke(Mono.error(new IllegalStateException("上游异常")));

        StepVerifier.create(result).expectError(IllegalStateException.class).verify();

        verify(asyncSyncService, never()).syncNeo4jAsync(anyString(), anyString());
        verify(asyncSyncService, never()).syncWarehouseAsync(any(), any());
    }

    private Mono<?> invoke(Mono<Result<?>> upstream) throws Throwable {
        ProceedingJoinPoint joinPoint = mock(ProceedingJoinPoint.class);
        MethodSignature signature = mock(MethodSignature.class);
        DataSync dataSync = mock(DataSync.class);

        when(joinPoint.proceed()).thenReturn(upstream);
        lenient().when(joinPoint.getSignature()).thenReturn(signature);
        lenient().when(signature.toShortString()).thenReturn("fixture.method");
        when(dataSync.description()).thenReturn("测试描述");

        Mono<?> result = (Mono<?>) aspect.handleDataSync(joinPoint, dataSync);
        return result.contextWrite(Context.of(
            UserContext.CONTEXT_KEY_USER_ID, 7L,
            UserContext.CONTEXT_KEY_USERNAME, "tester"));
    }
}

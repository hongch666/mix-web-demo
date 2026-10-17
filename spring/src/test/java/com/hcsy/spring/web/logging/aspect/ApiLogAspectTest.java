package com.hcsy.spring.web.logging.aspect;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import java.lang.reflect.Method;

import org.aspectj.lang.ProceedingJoinPoint;
import org.aspectj.lang.reflect.MethodSignature;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentCaptor;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;

import com.hcsy.spring.application.service.AsyncApiLogService;
import com.hcsy.spring.common.utils.SimpleLogger;
import com.hcsy.spring.common.utils.UserContext;
import com.hcsy.spring.entity.event.ApiLogEvent;
import com.hcsy.spring.web.logging.annotation.ApiLog;

import com.fasterxml.jackson.databind.ObjectMapper;
import reactor.core.publisher.Mono;
import reactor.test.StepVerifier;
import reactor.util.context.Context;

class ApiLogAspectTest {

    // 验证该场景的预期行为
    @Test
    @DisplayName("响应成功后发送接口日志并写入完整路径")
    void sendsLogAfterSuccess() throws Throwable {
        AsyncApiLogService service = mock(AsyncApiLogService.class);
        when(service.sendAsync(any(ApiLogEvent.class))).thenReturn(Mono.empty());
        ApiLogAspect aspect = new ApiLogAspect(mock(SimpleLogger.class), new ObjectMapper(), service);
        Method method = Fixture.class.getDeclaredMethod("get", Long.class);

        Mono<?> result = (Mono<?>) aspect.logAround(mockJoinPoint(method, Mono.just("ok")),
            method.getAnnotation(ApiLog.class));

        StepVerifier.create(result.contextWrite(Context.of(UserContext.CONTEXT_KEY_USER_ID, 1L,
            UserContext.CONTEXT_KEY_USERNAME, "u")))
            .expectNextMatches("ok"::equals).verifyComplete();

        ArgumentCaptor<ApiLogEvent> captor = ArgumentCaptor.forClass(ApiLogEvent.class);
        verify(service).sendAsync(captor.capture());
        ApiLogEvent event = captor.getValue();
        assertEquals("/fixture/item/{id}", event.getApiPath());
        assertEquals("GET", event.getApiMethod());
        assertEquals(1L, event.getUserId());
    }

    // 验证该场景的预期行为
    @Test
    @DisplayName("类路径与方法路径之间缺少分隔符时补齐斜杠")
    void joinsPathWithSeparator() throws Throwable {
        AsyncApiLogService service = mock(AsyncApiLogService.class);
        when(service.sendAsync(any(ApiLogEvent.class))).thenReturn(Mono.empty());
        ApiLogAspect aspect = new ApiLogAspect(mock(SimpleLogger.class), new ObjectMapper(), service);
        Method method = Fixture.class.getDeclaredMethod("list", Long.class);

        Mono<?> result = (Mono<?>) aspect.logAround(mockJoinPoint(method, Mono.just("ok")),
            method.getAnnotation(ApiLog.class));

        StepVerifier.create(result.contextWrite(Context.empty()))
            .expectNextMatches("ok"::equals).verifyComplete();

        ArgumentCaptor<ApiLogEvent> captor = ArgumentCaptor.forClass(ApiLogEvent.class);
        verify(service).sendAsync(captor.capture());
        assertEquals("/fixture/list/{id}", captor.getValue().getApiPath());
    }

    // 验证该场景的预期行为
    @Test
    @DisplayName("业务异常时同样发送接口日志")
    void sendsLogAfterError() throws Throwable {
        AsyncApiLogService service = mock(AsyncApiLogService.class);
        when(service.sendAsync(any(ApiLogEvent.class))).thenReturn(Mono.empty());
        ApiLogAspect aspect = new ApiLogAspect(mock(SimpleLogger.class), new ObjectMapper(), service);
        Method method = Fixture.class.getDeclaredMethod("get", Long.class);

        Mono<?> result = (Mono<?>) aspect.logAround(mockJoinPoint(method, Mono.error(new IllegalStateException("失败"))),
            method.getAnnotation(ApiLog.class));

        StepVerifier.create(result.contextWrite(Context.empty()))
            .expectError(IllegalStateException.class).verify();
        verify(service).sendAsync(any(ApiLogEvent.class));
    }

    private ProceedingJoinPoint mockJoinPoint(Method method, Mono<?> upstream) throws Throwable {
        ProceedingJoinPoint point = mock(ProceedingJoinPoint.class);
        MethodSignature signature = mock(MethodSignature.class);
        when(point.getSignature()).thenReturn(signature);
        when(signature.getMethod()).thenReturn(method);
        when(point.getArgs()).thenReturn(new Object[] { 7L });
        when(point.proceed()).thenReturn(upstream);
        return point;
    }

    @RequestMapping("/fixture")
    static class Fixture {

        @GetMapping("/item/{id}")
        @ApiLog("读取项目")
        Mono<String> get(Long id) {
            return Mono.just("ok");
        }

        @GetMapping("list/{id}")
        @ApiLog("读取列表")
        Mono<String> list(Long id) {
            return Mono.just("ok");
        }
    }
}

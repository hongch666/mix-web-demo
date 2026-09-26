package com.hcsy.spring.core.aspect;

import static org.mockito.Mockito.*;

import java.lang.reflect.Method;

import org.aspectj.lang.ProceedingJoinPoint;
import org.aspectj.lang.reflect.MethodSignature;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;

import com.hcsy.spring.api.service.AsyncApiLogService;
import com.hcsy.spring.common.utils.SimpleLogger;
import com.hcsy.spring.common.utils.UserContext;
import com.hcsy.spring.core.annotation.ApiLog;

import com.fasterxml.jackson.databind.ObjectMapper;
import reactor.core.publisher.Mono;
import reactor.test.StepVerifier;
import reactor.util.context.Context;

class ApiLogAspectTest {
    // 验证该场景的预期行为
    @Test
    @DisplayName("响应成功后发送 API 日志")
    void sendsLogAfterSuccess() throws Throwable {
        AsyncApiLogService service = mock(AsyncApiLogService.class);
        when(service.sendAsync(anyMap())).thenReturn(Mono.empty());
        ApiLogAspect aspect = new ApiLogAspect(mock(SimpleLogger.class), new ObjectMapper(), service);
        Method method = Fixture.class.getDeclaredMethod("get", Long.class);
        ProceedingJoinPoint point = mock(ProceedingJoinPoint.class);
        MethodSignature signature = mock(MethodSignature.class);
        when(point.getSignature()).thenReturn(signature);
        when(signature.getMethod()).thenReturn(method);
        when(point.getArgs()).thenReturn(new Object[] { 3L });
        when(point.proceed()).thenReturn(Mono.just("ok"));
        Mono<?> result = (Mono<?>) aspect.logAround(point, method.getAnnotation(ApiLog.class));
        StepVerifier.create(result.contextWrite(Context.of(UserContext.CONTEXT_KEY_USER_ID, 1L,
            UserContext.CONTEXT_KEY_USERNAME, "u")))
            .expectNextMatches("ok"::equals).verifyComplete();
        verify(service).sendAsync(anyMap());
    }

    @RequestMapping("/fixture")
    static class Fixture {
        @GetMapping("/item")
        @ApiLog("读取项目")
        Mono<String> get(Long id) {
            return Mono.just("ok");
        }
    }
}

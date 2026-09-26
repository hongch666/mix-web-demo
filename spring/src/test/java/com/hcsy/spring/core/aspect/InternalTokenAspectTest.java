package com.hcsy.spring.core.aspect;

import org.aspectj.lang.ProceedingJoinPoint;
import org.aspectj.lang.Signature;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import com.hcsy.spring.common.constants.HttpCode;
import com.hcsy.spring.common.exceptions.BusinessException;
import com.hcsy.spring.common.utils.InternalTokenUtil;
import com.hcsy.spring.common.utils.SimpleLogger;
import com.hcsy.spring.common.utils.UserContext;
import com.hcsy.spring.core.annotation.RequireInternalToken;

import static org.mockito.Mockito.*;

import reactor.core.publisher.Mono;
import reactor.test.StepVerifier;
import reactor.util.context.Context;

class InternalTokenAspectTest {
    // 验证该场景的预期行为
    @Test
    @DisplayName("缺少内部令牌时拒绝请求")
    void rejectsMissingToken() throws Throwable {
        InternalTokenUtil tokens = mock(InternalTokenUtil.class);
        ProceedingJoinPoint point = mock(ProceedingJoinPoint.class);
        when(point.proceed()).thenReturn(Mono.just("ok"));
        RequireInternalToken annotation = mock(RequireInternalToken.class);
        when(annotation.value()).thenReturn("");
        Mono<?> result = (Mono<?>) new InternalTokenAspect(tokens, mock(SimpleLogger.class))
            .validateInternalToken(point, annotation);
        StepVerifier.create(result)
            .expectErrorMatches(e -> e instanceof BusinessException b && b.getHttpStatus() == HttpCode.UNAUTHORIZED)
            .verify();
    }

    // 验证该场景的预期行为

    @Test
    @DisplayName("有效内部令牌允许业务继续执行")
    void acceptsValidToken() throws Throwable {
        InternalTokenUtil tokens = mock(InternalTokenUtil.class);
        when(tokens.extractServiceName("token")).thenReturn("orders");
        ProceedingJoinPoint point = mock(ProceedingJoinPoint.class);
        when(point.proceed()).thenReturn(Mono.just("ok"));
        when(point.getSignature()).thenReturn(mock(Signature.class));
        RequireInternalToken annotation = mock(RequireInternalToken.class);
        when(annotation.value()).thenReturn("orders");
        Mono<?> result = (Mono<?>) new InternalTokenAspect(tokens, mock(SimpleLogger.class))
            .validateInternalToken(point, annotation);
        StepVerifier.create(result.contextWrite(Context.of(UserContext.CONTEXT_KEY_INTERNAL_TOKEN, "token")))
            .expectNextMatches("ok"::equals).verifyComplete();
    }
}

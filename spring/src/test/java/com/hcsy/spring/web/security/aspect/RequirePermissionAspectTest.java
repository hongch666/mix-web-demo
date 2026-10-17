package com.hcsy.spring.web.security.aspect;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyLong;
import static org.mockito.Mockito.lenient;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import java.lang.reflect.Method;
import java.util.List;

import org.aspectj.lang.ProceedingJoinPoint;
import org.aspectj.lang.reflect.MethodSignature;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestParam;

import com.hcsy.spring.application.service.PermissionChecker;
import com.hcsy.spring.common.constants.BusinessType;
import com.hcsy.spring.common.constants.HttpCode;
import com.hcsy.spring.common.constants.Messages;
import com.hcsy.spring.common.constants.ParamSource;
import com.hcsy.spring.common.exceptions.BusinessException;
import com.hcsy.spring.common.utils.SimpleLogger;
import com.hcsy.spring.common.utils.UserContext;
import com.hcsy.spring.web.security.annotation.RequirePermission;

import reactor.core.publisher.Mono;
import reactor.test.StepVerifier;
import reactor.util.context.Context;

@ExtendWith(MockitoExtension.class)
class RequirePermissionAspectTest {

    @Mock
    private PermissionChecker permissionChecker;
    @Mock
    private SimpleLogger logger;

    private RequirePermissionAspect aspect;

    @BeforeEach
    void setUp() {
        aspect = new RequirePermissionAspect(permissionChecker, logger);
    }

    // 验证该场景的预期行为

    @Test
    @DisplayName("缺少用户上下文时拒绝访问")
    void rejectsMissingUserContext() throws Throwable {
        Mono<?> result = invoke("userQuery", new Class<?>[] { Long.class }, 7L);

        StepVerifier.create(result)
            .expectErrorMatches(error -> hasStatus(error, HttpCode.FORBIDDEN))
            .verify();
        verify(permissionChecker, never()).hasAnyRole(anyLong(), any());
    }

    // 验证该场景的预期行为

    @Test
    @DisplayName("本人访问时无需管理员角色即可放行")
    void allowsSelfAccess() throws Throwable {
        when(permissionChecker.hasAnyRole(7L, new String[] { "admin" })).thenReturn(Mono.just(false));
        when(permissionChecker.isOwner(7L, 7L, BusinessType.USER)).thenReturn(Mono.just(true));

        Mono<?> result = invoke("userQuery", new Class<?>[] { Long.class }, 7L)
            .contextWrite(Context.of(UserContext.CONTEXT_KEY_USER_ID, 7L));

        StepVerifier.create(result).expectNextMatches("ok"::equals).verifyComplete();
    }

    // 验证该场景的预期行为

    @Test
    @DisplayName("管理员可以访问其他用户")
    void allowsAdminAccess() throws Throwable {
        when(permissionChecker.hasAnyRole(7L, new String[] { "admin" })).thenReturn(Mono.just(true));

        Mono<?> result = invoke("userQuery", new Class<?>[] { Long.class }, 8L)
            .contextWrite(Context.of(UserContext.CONTEXT_KEY_USER_ID, 7L));

        StepVerifier.create(result).expectNextMatches("ok"::equals).verifyComplete();
        verify(permissionChecker, never()).isOwner(anyLong(), anyLong(), any());
    }

    // 验证该场景的预期行为

    @Test
    @DisplayName("普通用户不能访问其他用户")
    void rejectsOtherUserAccess() throws Throwable {
        when(permissionChecker.hasAnyRole(7L, new String[] { "admin" })).thenReturn(Mono.just(false));
        when(permissionChecker.isOwner(7L, 8L, BusinessType.USER)).thenReturn(Mono.just(false));

        Mono<?> result = invoke("userQuery", new Class<?>[] { Long.class }, 8L)
            .contextWrite(Context.of(UserContext.CONTEXT_KEY_USER_ID, 7L));

        StepVerifier.create(result)
            .expectErrorMatches(error -> hasStatus(error, HttpCode.FORBIDDEN))
            .verify();
    }

    // 验证该场景的预期行为

    @Test
    @DisplayName("文章所有者可以通过路径参数访问自己的文章")
    void allowsArticleOwner() throws Throwable {
        when(permissionChecker.hasAnyRole(7L, new String[] { "admin" })).thenReturn(Mono.just(false));
        when(permissionChecker.isOwner(7L, 21L, BusinessType.ARTICLE)).thenReturn(Mono.just(true));

        Mono<?> result = invoke("articlePath", new Class<?>[] { Long.class }, 21L)
            .contextWrite(Context.of(UserContext.CONTEXT_KEY_USER_ID, 7L));

        StepVerifier.create(result).expectNextMatches("ok"::equals).verifyComplete();
    }

    // 验证该场景的预期行为

    @Test
    @DisplayName("批量文章属于不同用户时拒绝操作")
    void rejectsBatchWithDifferentOwners() throws Throwable {
        when(permissionChecker.hasAnyRole(7L, new String[] { "admin" })).thenReturn(Mono.just(false));
        when(permissionChecker.resolveSharedOwner(List.of(21L, 22L), BusinessType.ARTICLE))
            .thenReturn(Mono.error(BusinessException.builder().httpStatus(HttpCode.BAD_REQUEST)
                .errorMessage(Messages.MULTIPLE_RESOURCE_OWNERS).build()));

        Mono<?> result = invoke("articleBatch", new Class<?>[] { String.class }, "21,22")
            .contextWrite(Context.of(UserContext.CONTEXT_KEY_USER_ID, 7L));

        StepVerifier.create(result)
            .expectErrorMatches(error -> hasStatus(error, HttpCode.BAD_REQUEST))
            .verify();
        verify(permissionChecker, never()).isOwner(anyLong(), anyLong(), any());
    }

    private Mono<?> invoke(String methodName, Class<?>[] parameterTypes, Object... arguments) throws Throwable {
        Method method = EndpointFixture.class.getDeclaredMethod(methodName, parameterTypes);
        ProceedingJoinPoint joinPoint = mock(ProceedingJoinPoint.class);
        MethodSignature signature = mock(MethodSignature.class);
        when(joinPoint.proceed()).thenReturn(Mono.just("ok"));
        lenient().when(joinPoint.getSignature()).thenReturn(signature);
        lenient().when(joinPoint.getArgs()).thenReturn(arguments);
        lenient().when(signature.getMethod()).thenReturn(method);
        RequirePermission permission = method.getAnnotation(RequirePermission.class);
        return (Mono<?>) aspect.checkPermission(joinPoint, permission);
    }

    private boolean hasStatus(Throwable error, int status) {
        return error instanceof BusinessException businessException
            && businessException.getHttpStatus() == status;
    }

    private static final class EndpointFixture {

        @RequirePermission(roles = { "admin" }, allowSelf = true, businessType = BusinessType.USER,
            paramSource = ParamSource.QUERY, paramName = "user_id")
        Mono<String> userQuery(@RequestParam("user_id") Long userId) {
            return Mono.just("ok");
        }

        @RequirePermission(roles = { "admin" }, allowSelf = true, businessType = BusinessType.ARTICLE,
            paramSource = ParamSource.PATH_SINGLE, paramName = "id")
        Mono<String> articlePath(@PathVariable("id") Long id) {
            return Mono.just("ok");
        }

        @RequirePermission(roles = { "admin" }, allowSelf = true, businessType = BusinessType.ARTICLE,
            paramSource = ParamSource.PATH_SINGLE, paramName = "ids")
        Mono<String> articleBatch(@PathVariable("ids") String ids) {
            return Mono.just("ok");
        }
    }
}

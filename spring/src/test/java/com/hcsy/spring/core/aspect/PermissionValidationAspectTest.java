package com.hcsy.spring.core.aspect;

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

import com.hcsy.spring.api.service.ArticleService;
import com.hcsy.spring.api.service.CommentsService;
import com.hcsy.spring.api.service.UserService;
import com.hcsy.spring.common.constants.HttpCode;
import com.hcsy.spring.common.exceptions.BusinessException;
import com.hcsy.spring.common.utils.SimpleLogger;
import com.hcsy.spring.common.utils.UserContext;
import com.hcsy.spring.core.annotation.RequirePermission;
import com.hcsy.spring.entity.po.Article;
import com.hcsy.spring.entity.po.User;

import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;
import reactor.test.StepVerifier;
import reactor.util.context.Context;

@ExtendWith(MockitoExtension.class)
class PermissionValidationAspectTest {

    @Mock
    private UserService userService;
    @Mock
    private ArticleService articleService;
    @Mock
    private CommentsService commentsService;
    @Mock
    private SimpleLogger logger;

    private PermissionValidationAspect aspect;

    @BeforeEach
    void setUp() {
        aspect = new PermissionValidationAspect(userService, articleService, commentsService, logger);
    }

    @Test
    @DisplayName("缺少用户上下文时拒绝访问")
    void rejectsMissingUserContext() throws Throwable {
        Mono<?> result = invoke("userQuery", new Class<?>[] { Long.class }, 7L);

        StepVerifier.create(result)
            .expectErrorMatches(error -> hasStatus(error, HttpCode.FORBIDDEN))
            .verify();
        verify(userService, never()).getById(anyLong());
    }

    @Test
    @DisplayName("本人访问时无需管理员角色即可放行")
    void allowsSelfAccess() throws Throwable {
        when(userService.getById(7L)).thenReturn(Mono.just(user(7L, "user")));

        Mono<?> result = invoke("userQuery", new Class<?>[] { Long.class }, 7L)
            .contextWrite(Context.of(UserContext.CONTEXT_KEY_USER_ID, 7L));

        StepVerifier.create(result).expectNextMatches("ok"::equals).verifyComplete();
    }

    @Test
    @DisplayName("管理员可以访问其他用户")
    void allowsAdminAccess() throws Throwable {
        when(userService.getById(7L)).thenReturn(Mono.just(user(7L, "admin")));

        Mono<?> result = invoke("userQuery", new Class<?>[] { Long.class }, 8L)
            .contextWrite(Context.of(UserContext.CONTEXT_KEY_USER_ID, 7L));

        StepVerifier.create(result).expectNextMatches("ok"::equals).verifyComplete();
        verify(articleService, never()).getById(anyLong());
        verify(commentsService, never()).getById(anyLong());
    }

    @Test
    @DisplayName("普通用户不能访问其他用户")
    void rejectsOtherUserAccess() throws Throwable {
        when(userService.getById(7L)).thenReturn(Mono.just(user(7L, "user")));

        Mono<?> result = invoke("userQuery", new Class<?>[] { Long.class }, 8L)
            .contextWrite(Context.of(UserContext.CONTEXT_KEY_USER_ID, 7L));

        StepVerifier.create(result)
            .expectErrorMatches(error -> hasStatus(error, HttpCode.FORBIDDEN))
            .verify();
    }

    @Test
    @DisplayName("文章所有者可以通过路径参数访问自己的文章")
    void allowsArticleOwner() throws Throwable {
        when(userService.getById(7L)).thenReturn(Mono.just(user(7L, "user")));
        when(articleService.getById(21L)).thenReturn(Mono.just(article(21L, 7L)));

        Mono<?> result = invoke("articlePath", new Class<?>[] { Long.class }, 21L)
            .contextWrite(Context.of(UserContext.CONTEXT_KEY_USER_ID, 7L));

        StepVerifier.create(result).expectNextMatches("ok"::equals).verifyComplete();
    }

    @Test
    @DisplayName("批量文章属于不同用户时拒绝操作")
    void rejectsBatchWithDifferentOwners() throws Throwable {
        when(userService.getById(7L)).thenReturn(Mono.just(user(7L, "user")));
        when(articleService.listByIds(List.of(21L, 22L)))
            .thenReturn(Flux.just(article(21L, 7L), article(22L, 8L)));

        Mono<?> result = invoke("articleBatch", new Class<?>[] { String.class }, "21,22")
            .contextWrite(Context.of(UserContext.CONTEXT_KEY_USER_ID, 7L));

        StepVerifier.create(result)
            .expectErrorMatches(error -> hasStatus(error, HttpCode.BAD_REQUEST))
            .verify();
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

    private User user(Long id, String role) {
        User user = new User();
        user.setId(id);
        user.setRole(role);
        return user;
    }

    private Article article(Long id, Long userId) {
        Article article = new Article();
        article.setId(id);
        article.setUserId(userId);
        return article;
    }

    private static final class EndpointFixture {
        @RequirePermission(roles = { "admin" }, allowSelf = true, businessType = "user",
            paramSource = "query", paramNames = { "user_id" })
        Mono<String> userQuery(@RequestParam("user_id") Long userId) {
            return Mono.just("ok");
        }

        @RequirePermission(roles = { "admin" }, allowSelf = true, businessType = "article",
            paramSource = "path_single", paramNames = { "id" })
        Mono<String> articlePath(@PathVariable("id") Long id) {
            return Mono.just("ok");
        }

        @RequirePermission(roles = { "admin" }, allowSelf = true, businessType = "article",
            paramSource = "path_single", paramNames = { "ids" })
        Mono<String> articleBatch(@PathVariable("ids") String ids) {
            return Mono.just("ok");
        }
    }
}

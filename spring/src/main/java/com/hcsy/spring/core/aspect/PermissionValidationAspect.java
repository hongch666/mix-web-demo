package com.hcsy.spring.core.aspect;

import java.lang.annotation.Annotation;
import java.lang.reflect.Method;
import java.util.Arrays;
import java.util.List;

import org.aspectj.lang.ProceedingJoinPoint;
import org.aspectj.lang.annotation.Around;
import org.aspectj.lang.annotation.Aspect;
import org.aspectj.lang.reflect.MethodSignature;
import org.springframework.core.DefaultParameterNameDiscoverer;
import org.springframework.core.ParameterNameDiscoverer;
import org.springframework.stereotype.Component;
import org.springframework.web.bind.annotation.PathVariable;

import com.hcsy.spring.api.service.ArticleService;
import com.hcsy.spring.api.service.CommentsService;
import com.hcsy.spring.api.service.UserService;
import com.hcsy.spring.common.constants.HttpCode;
import com.hcsy.spring.common.constants.Messages;
import com.hcsy.spring.common.exceptions.BusinessException;
import com.hcsy.spring.common.utils.SimpleLogger;
import com.hcsy.spring.common.utils.UserContext;
import com.hcsy.spring.core.annotation.RequirePermission;

import lombok.RequiredArgsConstructor;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

@Aspect
@Component
@RequiredArgsConstructor
public class PermissionValidationAspect {

    private final UserService userService;
    private final ArticleService articleService;
    private final CommentsService commentsService;
    private final SimpleLogger logger;
    private final ParameterNameDiscoverer parameterNameDiscoverer = new DefaultParameterNameDiscoverer();

    @Around("@annotation(requirePermission)")
    public Object checkPermission(ProceedingJoinPoint joinPoint, RequirePermission requirePermission)
            throws Throwable {
        Object result = joinPoint.proceed();
        if (!(result instanceof Mono<?> businessMono)) {
            return result;
        }
        return Mono.deferContextual(context -> {
            Long currentUserId = UserContext.getUserId(context);
            if (currentUserId == null) {
                logger.info(Messages.UNLOGIN_DEFAULT);
                return Mono.error(forbidden());
            }
            return validatePermission(joinPoint, requirePermission, currentUserId)
                    .then(businessMono);
        });
    }

    private Mono<Void> validatePermission(
            ProceedingJoinPoint joinPoint, RequirePermission permission, Long currentUserId) {
        return userService.getById(currentUserId)
                .filter(user -> Arrays.asList(permission.roles()).contains(user.getRole()))
                .doOnNext(ignored -> logger.info(Messages.ADMIN_PASS))
                .hasElement()
                .flatMap(roleAllowed -> {
                    if (roleAllowed) {
                        return Mono.empty();
                    }
                    if (!permission.allowSelf()) {
                        return Mono.error(forbidden());
                    }
                    return resolveTargetResourceId(joinPoint, permission)
                            .flatMap(targetId -> checkOwnership(currentUserId, targetId, permission.businessType()))
                            .filter(Boolean.TRUE::equals)
                            .switchIfEmpty(Mono.error(forbidden()))
                            .then();
                });
    }

    private Mono<Long> resolveTargetResourceId(ProceedingJoinPoint joinPoint, RequirePermission permission) {
        String paramSource = permission.paramSource();
        String parameterName = permission.paramNames().length == 0 ? "id" : permission.paramNames()[0];
        if ("path_single".equals(paramSource) || "path_multi".equals(paramSource)) {
            Object value = getPathParameter(joinPoint, parameterName);
            if (value instanceof String text && text.contains(",")) {
                return validateBatchOwnership(text, permission.businessType());
            }
            return Mono.justOrEmpty(toLong(value));
        }
        if ("body".equals(paramSource)) {
            Object body = getBody(joinPoint, parameterName);
            return extractTargetFromBody(body, parameterName);
        }
        return Mono.empty();
    }

    @SuppressWarnings("null")
    private Mono<Long> validateBatchOwnership(String ids, String businessType) {
        List<Long> resourceIds;
        try {
            resourceIds = Arrays.stream(ids.split(","))
                    .map(String::trim)
                    .filter(value -> !value.isEmpty())
                    .map(Long::valueOf)
                    .distinct()
                    .toList();
        } catch (NumberFormatException error) {
            return Mono.error(BusinessException.builder().httpStatus(HttpCode.BAD_REQUEST)
                    .errorMessage(Messages.TARGET_FAIL).cause(error).build());
        }
        if (resourceIds.isEmpty()) {
            return Mono.empty();
        }

        Flux<Long> owners;
        if ("article".equals(businessType)) {
            owners = articleService.listByIds(resourceIds)
                    .switchIfEmpty(Mono.error(notFound(Messages.UNDEFINED_ARTICLES)))
                    .map(article -> article.getUserId());
        } else if ("comment".equals(businessType)) {
            owners = Flux.fromIterable(resourceIds)
                    .concatMap(id -> commentsService.getById(id)
                            .switchIfEmpty(Mono.error(notFound(Messages.COMMENT_ID + id))))
                    .map(comment -> comment.getUserId());
        } else {
            return Mono.empty();
        }
        return owners.collectList().flatMap(ownerIds -> {
            if (ownerIds.size() != resourceIds.size() || ownerIds.stream().anyMatch(id -> id == null)) {
                return Mono.error(notFound(Messages.NO_SOURCE));
            }
            Long owner = ownerIds.get(0);
            if (ownerIds.stream().anyMatch(id -> !owner.equals(id))) {
                return Mono.error(BusinessException.builder().httpStatus(HttpCode.BAD_REQUEST)
                        .errorMessage(Messages.MULTIPLE_RESOURCE_OWNERS).build());
            }
            return Mono.just(owner);
        });
    }

    private Mono<Long> extractTargetFromBody(Object body, String parameterName) {
        if (body == null) {
            return Mono.empty();
        }
        Long id = invokeLongGetter(body, "getId");
        if (id != null && ("id".equals(parameterName) || parameterName.endsWith("Id"))) {
            return Mono.just(id);
        }
        Long userId = invokeLongGetter(body, "getUserId");
        if (userId != null) {
            return Mono.just(userId);
        }
        String username = invokeStringGetter(body, "getUsername");
        if (username != null) {
            return userService.findByUsername(username).map(user -> user.getId());
        }
        return Mono.empty();
    }

    private Mono<Boolean> checkOwnership(Long currentUserId, Long targetResourceId, String businessType) {
        if ("user".equals(businessType)) {
            return Mono.just(currentUserId.equals(targetResourceId));
        }
        if ("article".equals(businessType)) {
            return articleService.getById(targetResourceId)
                    .map(article -> currentUserId.equals(article.getUserId()))
                    .defaultIfEmpty(false);
        }
        if ("comment".equals(businessType)) {
            return commentsService.getById(targetResourceId)
                    .map(comment -> currentUserId.equals(comment.getUserId()))
                    .defaultIfEmpty(false);
        }
        return Mono.just(false);
    }

    private Object getPathParameter(ProceedingJoinPoint joinPoint, String requestedName) {
        Method method = ((MethodSignature) joinPoint.getSignature()).getMethod();
        Object[] arguments = joinPoint.getArgs();
        Annotation[][] annotations = method.getParameterAnnotations();
        for (int index = 0; index < annotations.length; index++) {
            for (Annotation annotation : annotations[index]) {
                if (annotation instanceof PathVariable pathVariable) {
                    String name = pathVariable.value().isEmpty() ? pathVariable.name() : pathVariable.value();
                    if (name.equals(requestedName) || "id".equals(requestedName)) {
                        return arguments[index];
                    }
                }
            }
        }
        return null;
    }

    private Object getBody(ProceedingJoinPoint joinPoint, String requestedName) {
        @SuppressWarnings("null")
        String[] names = parameterNameDiscoverer.getParameterNames(
                ((MethodSignature) joinPoint.getSignature()).getMethod());
        Object[] arguments = joinPoint.getArgs();
        if (names != null) {
            for (int index = 0; index < names.length; index++) {
                if (requestedName.equals(names[index]) || "dto".equalsIgnoreCase(names[index])) {
                    return arguments[index];
                }
            }
        }
        return arguments.length == 0 ? null : arguments[0];
    }

    private Long invokeLongGetter(Object source, String methodName) {
        try {
            Object value = source.getClass().getMethod(methodName).invoke(source);
            return toLong(value);
        } catch (ReflectiveOperationException ignored) {
            return null;
        }
    }

    private String invokeStringGetter(Object source, String methodName) {
        try {
            Object value = source.getClass().getMethod(methodName).invoke(source);
            return value instanceof String text ? text : null;
        } catch (ReflectiveOperationException ignored) {
            return null;
        }
    }

    private Long toLong(Object value) {
        if (value instanceof Number number) {
            return number.longValue();
        }
        if (value instanceof String text && !text.contains(",")) {
            try {
                return Long.parseLong(text);
            } catch (NumberFormatException ignored) {
                return null;
            }
        }
        return null;
    }

    private BusinessException forbidden() {
        return BusinessException.builder().httpStatus(HttpCode.FORBIDDEN).errorMessage(Messages.NO_PERMISION).build();
    }

    private BusinessException notFound(String message) {
        return BusinessException.builder().httpStatus(HttpCode.NOT_FOUND).errorMessage(message).build();
    }
}

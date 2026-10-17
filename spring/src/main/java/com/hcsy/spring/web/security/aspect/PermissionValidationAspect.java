package com.hcsy.spring.web.security.aspect;

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
import org.springframework.core.annotation.Order;
import org.springframework.stereotype.Component;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestParam;

import com.hcsy.spring.application.service.PermissionChecker;
import com.hcsy.spring.common.constants.BusinessType;
import com.hcsy.spring.common.constants.HttpCode;
import com.hcsy.spring.common.constants.Messages;
import com.hcsy.spring.common.exceptions.BusinessException;
import com.hcsy.spring.common.utils.SimpleLogger;
import com.hcsy.spring.common.utils.SyncEventCollector;
import com.hcsy.spring.common.utils.UserContext;
import com.hcsy.spring.web.security.annotation.RequirePermission;

import lombok.RequiredArgsConstructor;
import reactor.core.publisher.Mono;

/**
 * 权限校验切面
 * 只负责从切点提取目标资源标识与编排校验顺序，角色读取和归属判定由 PermissionChecker 承担
 */
@Aspect
@Component
@Order(20)
@RequiredArgsConstructor
public class PermissionValidationAspect {

    private final PermissionChecker permissionChecker;
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
            return authorize(joinPoint, requirePermission, currentUserId).then(businessMono);
        });
    }

    /**
     * 角色校验先于归属校验，角色不匹配且不允许操作自身数据时直接拒绝
     */
    private Mono<Void> authorize(ProceedingJoinPoint joinPoint, RequirePermission permission, Long currentUserId) {
        return permissionChecker.hasAnyRole(currentUserId, permission.roles())
            .flatMap(roleAllowed -> {
                if (roleAllowed) {
                    logger.info(Messages.ADMIN_PASS);
                    return Mono.empty();
                }
                if (!permission.allowSelf()) {
                    return Mono.error(forbidden());
                }
                return checkOwnership(joinPoint, permission, currentUserId)
                    .filter(Boolean.TRUE::equals)
                    .switchIfEmpty(Mono.error(forbidden()))
                    .then();
            });
    }

    /**
     * 按注解声明的参数来源解析目标资源并校验归属
     */
    private Mono<Boolean> checkOwnership(ProceedingJoinPoint joinPoint, RequirePermission permission,
        Long currentUserId) {
        BusinessType businessType = permission.businessType();
        String parameterName = permission.paramName();
        return switch (permission.paramSource()) {
            case PATH_SINGLE, PATH_MULTI -> checkPathOwnership(joinPoint, permission, currentUserId, parameterName);
            case BODY -> resolveTargetFromBody(joinPoint, parameterName)
                .flatMap(targetId -> permissionChecker.isOwner(currentUserId, targetId, businessType))
                .defaultIfEmpty(false);
            case QUERY -> permissionChecker.isOwner(currentUserId,
                toLong(getQueryParameter(joinPoint, parameterName)), businessType);
        };
    }

    /**
     * 路径参数可能是单个标识，也可能是逗号分隔的批量标识
     * 批量场景先解析出唯一所有者，再与当前用户比对
     */
    private Mono<Boolean> checkPathOwnership(ProceedingJoinPoint joinPoint, RequirePermission permission,
        Long currentUserId, String parameterName) {
        Object value = getPathParameter(joinPoint, parameterName);
        if (value instanceof String text && text.contains(",")) {
            return parseIds(text)
                .flatMap(ids -> ids.isEmpty()
                    ? Mono.just(false)
                    : permissionChecker.resolveSharedOwner(ids, permission.businessType())
                        .map(owner -> currentUserId.equals(owner)))
                .defaultIfEmpty(false);
        }
        return permissionChecker.isOwner(currentUserId, toLong(value), permission.businessType());
    }

    private Mono<List<Long>> parseIds(String ids) {
        try {
            return Mono.just(Arrays.stream(ids.split(","))
                .map(String::trim)
                .filter(value -> !value.isEmpty())
                .map(Long::valueOf)
                .distinct()
                .toList());
        } catch (NumberFormatException error) {
            return Mono.error(BusinessException.builder().httpStatus(HttpCode.BAD_REQUEST)
                .errorMessage(Messages.TARGET_FAIL).cause(error).build());
        }
    }

    private Mono<Long> resolveTargetFromBody(ProceedingJoinPoint joinPoint, String parameterName) {
        Object body = getBody(joinPoint, parameterName);
        if (body == null) {
            return Mono.empty();
        }
        Long id = SyncEventCollector.readLong(body, "id");
        if (id != null && ("id".equals(parameterName) || parameterName.endsWith("Id"))) {
            return Mono.just(id);
        }
        Long userId = SyncEventCollector.readLong(body, "userId");
        if (userId != null) {
            return Mono.just(userId);
        }
        String username = SyncEventCollector.readString(body, "username");
        return username == null ? Mono.empty() : permissionChecker.resolveUserIdByUsername(username);
    }

    private Object getQueryParameter(ProceedingJoinPoint joinPoint, String requestedName) {
        Method method = ((MethodSignature) joinPoint.getSignature()).getMethod();
        Object[] arguments = joinPoint.getArgs();
        Annotation[][] annotations = method.getParameterAnnotations();
        for (int index = 0; index < annotations.length; index++) {
            for (Annotation annotation : annotations[index]) {
                if (annotation instanceof RequestParam requestParam) {
                    String name = requestParam.value().isEmpty() ? requestParam.name() : requestParam.value();
                    if (name.equals(requestedName)) {
                        return arguments[index];
                    }
                }
            }
        }
        return null;
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
        return BusinessException.builder().httpStatus(HttpCode.FORBIDDEN).errorMessage(Messages.NO_PERMISSION).build();
    }
}

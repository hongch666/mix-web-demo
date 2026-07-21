package com.hcsy.spring.core.aspect;

import java.lang.reflect.Method;
import java.util.Arrays;

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
import com.hcsy.spring.common.exceptions.BusinessException;
import com.hcsy.spring.common.constants.Messages;
import com.hcsy.spring.common.constants.HttpCode;
import com.hcsy.spring.common.utils.SimpleLogger;
import com.hcsy.spring.common.utils.UserContext;
import com.hcsy.spring.core.annotation.RequirePermission;
import com.hcsy.spring.entity.po.Article;
import com.hcsy.spring.entity.po.Comments;
import com.hcsy.spring.entity.po.User;

import lombok.RequiredArgsConstructor;
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
        // 包装返回的 Mono，在链内用 deferContextual 获取上下文
        Object result = joinPoint.proceed();
        if (result instanceof Mono<?> monoResult) {
            return monoResult
                .flatMap(res -> Mono.deferContextual(ctx -> {
                    try {
                        // 从 Reactor Context 获取用户信息
                        Long currentUserId = UserContext.getUserId(ctx);
                        if (currentUserId == null) {
                            currentUserId = -1L;
                            logger.info(Messages.UNLOGIN_DEFAULT);
                        }

                        // 检查管理员权限
                        if (currentUserId > 0) {
                            User currentUser = userService.getById(currentUserId);
                            if (currentUser != null && Arrays.asList(requirePermission.roles()).contains(currentUser.getRole())) {
                                logger.info(Messages.ADMIN_PASS);
                                return Mono.just(res);
                            }
                        }

                        // 获取目标资源ID
                        Long targetResourceId = getTargetResourceId(joinPoint, requirePermission, currentUserId);
                        logger.info(Messages.TARGET_SOURCE,
                                currentUserId, requirePermission.businessType(), requirePermission.paramSource(), targetResourceId);

                        // 根据业务类型校验权限
                        if (requirePermission.allowSelf()) {
                            if (!checkOwnership(currentUserId, targetResourceId, requirePermission.businessType())) {
                                throw BusinessException.builder().httpStatus(HttpCode.FORBIDDEN).errorMessage(Messages.NO_PERMISION).build();
                            }
                        } else {
                            throw BusinessException.builder().httpStatus(HttpCode.FORBIDDEN).errorMessage(Messages.NO_PERMISION).build();
                        }

                        return Mono.just(res);
                    } catch (Exception e) {
                        logger.error(Messages.PERMITION_FAIL + e.getMessage());
                        return Mono.error(e);
                    }
                }));
        }
        return result;
    }

    /**
     * 获取目标资源ID，支持多种参数来源
     */
    private Long getTargetResourceId(ProceedingJoinPoint joinPoint, RequirePermission requirePermission,
            Long currentUserId) {
        String paramSource = requirePermission.paramSource();
        String[] paramNames = requirePermission.paramNames();

        try {
            if ("path_single".equals(paramSource)) {
                return getPathSingleParam(joinPoint, paramNames[0]);
            } else if ("path_multi".equals(paramSource)) {
                return getPathMultiParams(joinPoint, paramNames, requirePermission.businessType(), currentUserId);
            } else if ("body".equals(paramSource)) {
                return getBodyParam(joinPoint, paramNames[0], requirePermission.businessType());
            }
        } catch (Exception e) {
            logger.error(Messages.TARGET_FAIL + e.getMessage(), e);
        }

        return null;
    }

    /**
     * 获取路径单个参数
     */
    private Long getPathSingleParam(ProceedingJoinPoint joinPoint, String paramName) {
        try {
            Object[] args = joinPoint.getArgs();
            MethodSignature methodSignature = (MethodSignature) joinPoint.getSignature();
            Method method = methodSignature.getMethod();
            java.lang.annotation.Annotation[][] paramAnnotations = method.getParameterAnnotations();

            for (int i = 0; i < paramAnnotations.length; i++) {
                for (java.lang.annotation.Annotation annotation : paramAnnotations[i]) {
                    if (annotation instanceof PathVariable) {
                        PathVariable pathVar = (PathVariable) annotation;
                        String name = pathVar.value().isEmpty() ? pathVar.name() : pathVar.value();

                        if (name.equals(paramName) || "id".equals(paramName)) {
                            Object argValue = args[i];
                            if (argValue instanceof Long) {
                                Long id = (Long) argValue;
                                logger.info(Messages.FUNCTION_PATH, paramName, id);
                                return id;
                            } else if (argValue instanceof String) {
                                try {
                                    Long id = Long.parseLong((String) argValue);
                                    logger.info(Messages.FUNCTION_PATH, paramName, id);
                                    return id;
                                } catch (NumberFormatException e) {
                                    logger.warning(Messages.FUNCTION_PATH_FAIL + argValue);
                                }
                            } else if (argValue instanceof Integer) {
                                Long id = ((Integer) argValue).longValue();
                                logger.info(Messages.FUNCTION_PATH, paramName, id);
                                return id;
                            }
                        }
                    }
                }
            }
        } catch (Exception e) {
            logger.warning(Messages.SINGLE_PATH + e.getMessage());
        }

        return null;
    }

    /**
     * 获取路径多个参数，处理特殊场景如 /comments/batch/{ids}
     */
    private Long getPathMultiParams(ProceedingJoinPoint joinPoint, String[] paramNames, String businessType,
            Long currentUserId) {
        try {
            Object[] args = joinPoint.getArgs();
            MethodSignature methodSignature = (MethodSignature) joinPoint.getSignature();
            Method method = methodSignature.getMethod();
            java.lang.annotation.Annotation[][] paramAnnotations = method.getParameterAnnotations();

            String batchIdsStr = null;
            for (int i = 0; i < paramAnnotations.length; i++) {
                for (java.lang.annotation.Annotation annotation : paramAnnotations[i]) {
                    if (annotation instanceof PathVariable) {
                        PathVariable pathVar = (PathVariable) annotation;
                        String name = pathVar.value().isEmpty() ? pathVar.name() : pathVar.value();

                        if ("ids".equals(name) || (paramNames.length > 0 && name.equals(paramNames[0]))) {
                            Object argValue = args[i];
                            if (argValue instanceof String) {
                                batchIdsStr = (String) argValue;
                                break;
                            }
                        }
                    }
                }
                if (batchIdsStr != null)
                    break;
            }

            if (batchIdsStr != null && batchIdsStr.contains(",")) {
                String[] ids = batchIdsStr.split(",");
                Long ownerUserId = null;

                if ("comment".equals(businessType)) {
                    for (String idStr : ids) {
                        idStr = idStr.trim();
                        if (!idStr.isEmpty()) {
                            Long commentId = Long.parseLong(idStr);
                            Comments comment = commentsService.getById(commentId);
                            if (comment == null) {
                                throw BusinessException.builder().httpStatus(HttpCode.NOT_FOUND).errorMessage(Messages.COMMENT_ID + commentId).build();
                            }
                            if (comment.getUserId() == null) {
                                throw BusinessException.builder().httpStatus(HttpCode.NOT_FOUND).errorMessage(Messages.COMMENT_NO_USER + commentId).build();
                            }
                            if (ownerUserId != null && !ownerUserId.equals(comment.getUserId())) {
                                throw BusinessException.builder().httpStatus(HttpCode.BAD_REQUEST).errorMessage(Messages.COMMENT_MULTI_USER).build();
                            }
                            ownerUserId = comment.getUserId();
                        }
                    }
                    if (!currentUserId.equals(ownerUserId)) {
                        throw BusinessException.builder().httpStatus(HttpCode.FORBIDDEN).errorMessage(Messages.NO_PERMISION).build();
                    }
                    logger.info(Messages.FUNCTION_COMMENT, ownerUserId);
                } else if ("article".equals(businessType)) {
                    for (String idStr : ids) {
                        idStr = idStr.trim();
                        if (!idStr.isEmpty()) {
                            Long articleId = Long.parseLong(idStr);
                            Article article = articleService.getById(articleId);
                            if (article == null) {
                                throw BusinessException.builder().httpStatus(HttpCode.NOT_FOUND).errorMessage(Messages.ARTICLE_ID + articleId).build();
                            }
                            if (article.getUserId() == null) {
                                throw BusinessException.builder().httpStatus(HttpCode.NOT_FOUND).errorMessage(Messages.ARTICLE_NO_USER + articleId).build();
                            }
                            if (ownerUserId != null && !ownerUserId.equals(article.getUserId())) {
                                throw BusinessException.builder().httpStatus(HttpCode.BAD_REQUEST).errorMessage(Messages.ARTICLE_MULTI_USER).build();
                            }
                            ownerUserId = article.getUserId();
                        }
                    }
                    if (!currentUserId.equals(ownerUserId)) {
                        throw BusinessException.builder().httpStatus(HttpCode.FORBIDDEN).errorMessage(Messages.NO_PERMISION).build();
                    }
                    logger.info(Messages.FUNCTION_ARTICLE, ownerUserId);
                }
                return currentUserId;
            }

        } catch (Exception e) {
            logger.warning(Messages.MULTI_PATH + e.getMessage());
        }

        return null;
    }

    /**
     * 获取请求体参数
     */
    private Long getBodyParam(ProceedingJoinPoint joinPoint, String paramName, String businessType) {
        try {
            Object[] args = joinPoint.getArgs();
            String[] paramNames = getParameterNames(joinPoint);

            for (int i = 0; i < paramNames.length; i++) {
                if (paramNames[i].equals(paramName) || paramNames[i].equals("dto") || paramNames[i].equals("DTO")) {
                    Object obj = args[i];
                    return extractUserIdFromObject(obj, paramName, businessType);
                }
            }

            if (args.length > 0) {
                return extractUserIdFromObject(args[0], paramName, businessType);
            }
        } catch (Exception e) {
            logger.warning(Messages.BODY_GET + e.getMessage());
        }

        return null;
    }

    /**
     * 从对象中提取用户ID
     */
    private Long extractUserIdFromObject(Object obj, String paramName, String businessType) throws Exception {
        if (obj == null) {
            return null;
        }

        try {
            if ("id".equals(paramName) || paramName.contains("Id")) {
                Method idMethod = tryGetMethod(obj, "getId");
                if (idMethod != null) {
                    Object idValue = idMethod.invoke(obj);
                    if (idValue instanceof Integer) {
                        return ((Integer) idValue).longValue();
                    } else if (idValue instanceof Long) {
                        return (Long) idValue;
                    }
                }
            }

            Method usernameMethod = tryGetMethod(obj, "getUsername");
            if (usernameMethod != null) {
                String username = (String) usernameMethod.invoke(obj);
                if (username != null) {
                    User user = userService.findByUsername(username);
                    if (user != null) {
                        logger.info(Messages.USERNAME_ID, username, user.getId());
                        return user.getId();
                    }
                }
            }

            Method userIdMethod = tryGetMethod(obj, "getUserId");
            if (userIdMethod != null) {
                Object userIdValue = userIdMethod.invoke(obj);
                if (userIdValue instanceof Long) {
                    return (Long) userIdValue;
                } else if (userIdValue instanceof Integer) {
                    return ((Integer) userIdValue).longValue();
                }
            }

        } catch (Exception e) {
            logger.warning(Messages.OBJECT_PARAM + e.getMessage());
        }

        return null;
    }

    /**
     * 尝试获取指定方法
     */
    private Method tryGetMethod(Object obj, String methodName) {
        try {
            return obj.getClass().getMethod(methodName);
        } catch (NoSuchMethodException e) {
            return null;
        }
    }

    /**
     * 检查资源所有权
     */
    private boolean checkOwnership(Long currentUserId, Long targetResourceId, String businessType) {
        if (targetResourceId == null) {
            logger.warning(Messages.NO_SOURCE);
            return false;
        }

        if ("user".equals(businessType)) {
            return currentUserId.equals(targetResourceId);
        } else if ("article".equals(businessType)) {
            if (currentUserId.equals(targetResourceId)) {
                return true;
            }
            Article article = articleService.getById(targetResourceId);
            if (article != null) {
                return currentUserId.equals(article.getUserId());
            }
        } else if ("comment".equals(businessType)) {
            if (currentUserId.equals(targetResourceId)) {
                return true;
            }
            Comments comment = commentsService.getById(targetResourceId);
            if (comment != null) {
                return currentUserId.equals(comment.getUserId());
            }
        } else if ("category".equals(businessType) || "subcategory".equals(businessType)) {
            return false;
        }

        return false;
    }

    /**
     * 获取方法参数名
     */
    @SuppressWarnings("null")
    private String[] getParameterNames(ProceedingJoinPoint joinPoint) {
        try {
            MethodSignature methodSignature = (MethodSignature) joinPoint.getSignature();
            Method method = methodSignature.getMethod();

            String[] parameterNames = parameterNameDiscoverer.getParameterNames(method);

            if (parameterNames != null) {
                return parameterNames;
            }

            logger.warning(Messages.PARAM_NAME);
            return new String[] {};

        } catch (Exception e) {
            logger.warning(Messages.PARAM_NAME + e.getMessage());
            return new String[] {};
        }
    }
}

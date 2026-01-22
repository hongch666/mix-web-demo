package com.hcsy.spring.common.aspect;

import com.hcsy.spring.api.service.CommentsService;
import com.hcsy.spring.api.service.UserService;
import com.hcsy.spring.api.service.ArticleService;
import com.hcsy.spring.common.annotation.RequirePermission;
import com.hcsy.spring.common.exceptions.BusinessException;
import com.hcsy.spring.common.utils.SimpleLogger;
import com.hcsy.spring.common.utils.UserContext;
import com.hcsy.spring.entity.po.Comments;
import com.hcsy.spring.entity.po.User;
import com.hcsy.spring.entity.po.Article;

import jakarta.servlet.http.HttpServletRequest;
import lombok.RequiredArgsConstructor;
import org.aspectj.lang.ProceedingJoinPoint;
import org.aspectj.lang.annotation.Around;
import org.aspectj.lang.annotation.Aspect;
import org.aspectj.lang.reflect.MethodSignature;
import org.springframework.core.DefaultParameterNameDiscoverer;
import org.springframework.core.ParameterNameDiscoverer;
import org.springframework.stereotype.Component;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.context.request.RequestContextHolder;
import org.springframework.web.context.request.ServletRequestAttributes;

import java.lang.reflect.Method;
import java.util.Arrays;

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
        try {
            // 1. 获取当前用户ID，未登录使用-1
            Long currentUserId = UserContext.getUserId();
            if (currentUserId == null) {
                currentUserId = -1L;
                logger.info("用户未登录，使用默认用户ID: -1");
            }

            // 2. 检查管理员权限
            if (currentUserId > 0) {
                User currentUser = userService.getById(currentUserId);
                if (currentUser != null && Arrays.asList(requirePermission.roles()).contains(currentUser.getRole())) {
                    logger.info("用户具有管理员权限，直接通过");
                    return joinPoint.proceed();
                }
            }

            // 3. 获取目标资源ID
            Long targetResourceId = getTargetResourceId(joinPoint, requirePermission);
            logger.info("当前用户ID: %d, 业务类型: %s, 参数来源: %s, 目标资源ID: %s",
                    currentUserId, requirePermission.businessType(), requirePermission.paramSource(), targetResourceId);

            // 4. 根据业务类型校验权限
            if (requirePermission.allowSelf()) {
                // 允许个人操作自己的数据
                if (!checkOwnership(currentUserId, targetResourceId, requirePermission.businessType())) {
                    throw new RuntimeException("权限不足，无法执行此操作");
                }
            } else {
                // 不允许操作自己，仅管理员能执行（权限已在步骤2检查）
                throw new RuntimeException("权限不足，无法执行此操作");
            }

            return joinPoint.proceed();

        } catch (RuntimeException e) {
            logger.error("权限检查失败: " + e.getMessage());
            throw e;
        } catch (Throwable e) {
            logger.error("权限检查发生异常", e);
            throw new RuntimeException("权限检查异常", e);
        }
    }

    /**
     * 获取目标资源ID，支持多种参数来源
     */
    private Long getTargetResourceId(ProceedingJoinPoint joinPoint, RequirePermission requirePermission) {
        String paramSource = requirePermission.paramSource();
        String[] paramNames = requirePermission.paramNames();

        try {
            if ("path_single".equals(paramSource)) {
                // 路径单个参数：如 /users/{id}
                return getPathSingleParam(joinPoint, paramNames[0]);
            } else if ("path_multi".equals(paramSource)) {
                // 路径多个参数：如 /articles/{articleId}/comments/{commentId}
                return getPathMultiParams(joinPoint, paramNames, requirePermission.businessType());
            } else if ("body".equals(paramSource)) {
                // 请求体参数
                return getBodyParam(joinPoint, paramNames[0], requirePermission.businessType());
            }
        } catch (Exception e) {
            logger.error("获取目标资源ID失败: " + e.getMessage(), e);
        }

        return null;
    }

    /**
     * 获取路径单个参数
     */
    private Long getPathSingleParam(ProceedingJoinPoint joinPoint, String paramName) {
        try {
            // 先尝试从方法参数中获取 @PathVariable 标注的参数
            Object[] args = joinPoint.getArgs();
            MethodSignature methodSignature = (MethodSignature) joinPoint.getSignature();
            Method method = methodSignature.getMethod();
            java.lang.annotation.Annotation[][] paramAnnotations = method.getParameterAnnotations();
            
            for (int i = 0; i < paramAnnotations.length; i++) {
                for (java.lang.annotation.Annotation annotation : paramAnnotations[i]) {
                    if (annotation instanceof PathVariable) {
                        PathVariable pathVar = (PathVariable) annotation;
                        String name = pathVar.value().isEmpty() ? pathVar.name() : pathVar.value();
                        
                        // 如果参数名匹配或是通用的id参数
                        if (name.equals(paramName) || "id".equals(paramName)) {
                            Object argValue = args[i];
                            if (argValue instanceof Long) {
                                Long id = (Long) argValue;
                                logger.info("从方法参数获取路径参数 %s = %d", paramName, id);
                                return id;
                            } else if (argValue instanceof String) {
                                try {
                                    Long id = Long.parseLong((String) argValue);
                                    logger.info("从方法参数获取路径参数 %s = %d", paramName, id);
                                    return id;
                                } catch (NumberFormatException e) {
                                    logger.warning("路径参数转换失败: " + argValue);
                                }
                            } else if (argValue instanceof Integer) {
                                Long id = ((Integer) argValue).longValue();
                                logger.info("从方法参数获取路径参数 %s = %d", paramName, id);
                                return id;
                            }
                        }
                    }
                }
            }
            
            // 备用方案：从URL中提取最后一个路径段作为ID
            ServletRequestAttributes attributes = (ServletRequestAttributes) RequestContextHolder
                    .getRequestAttributes();
            if (attributes != null) {
                HttpServletRequest request = attributes.getRequest();
                String pathVariable = request.getRequestURI();
                // 移除查询参数
                if (request.getQueryString() != null) {
                    pathVariable = pathVariable.split("\\?")[0];
                }

                String[] parts = pathVariable.split("/");
                // 从路径的最后一个非空段提取ID
                for (int i = parts.length - 1; i >= 0; i--) {
                    if (!parts[i].isEmpty()) {
                        try {
                            // 尝试将最后一个路径段转换为ID
                            Long id = Long.parseLong(parts[i]);
                            logger.info("从URL路径获取ID: %d", id);
                            return id;
                        } catch (NumberFormatException e) {
                            // 如果最后一个不是数字，说明这不是ID参数，返回null
                            logger.warning("URL最后一个路径段不是数字: %s", parts[i]);
                            return null;
                        }
                    }
                }
            }
        } catch (Exception e) {
            logger.warning("获取路径单个参数失败: " + e.getMessage());
        }

        return null;
    }

    /**
     * 获取路径多个参数，处理特殊场景如 /comments/batch/{ids}
     */
    private Long getPathMultiParams(ProceedingJoinPoint joinPoint, String[] paramNames, String businessType) {
        try {
            Object[] args = joinPoint.getArgs();
            MethodSignature methodSignature = (MethodSignature) joinPoint.getSignature();
            Method method = methodSignature.getMethod();
            java.lang.annotation.Annotation[][] paramAnnotations = method.getParameterAnnotations();
            
            // 先尝试从方法参数中获取批量ID参数
            String batchIdsStr = null;
            for (int i = 0; i < paramAnnotations.length; i++) {
                for (java.lang.annotation.Annotation annotation : paramAnnotations[i]) {
                    if (annotation instanceof PathVariable) {
                        PathVariable pathVar = (PathVariable) annotation;
                        String name = pathVar.value().isEmpty() ? pathVar.name() : pathVar.value();
                        
                        // 查找 ids 或 paramNames[0] 参数
                        if ("ids".equals(name) || (paramNames.length > 0 && name.equals(paramNames[0]))) {
                            Object argValue = args[i];
                            if (argValue instanceof String) {
                                batchIdsStr = (String) argValue;
                                break;
                            }
                        }
                    }
                }
                if (batchIdsStr != null) break;
            }
            
            if (batchIdsStr != null && batchIdsStr.contains(",")) {
                // 批量删除的情况
                String[] ids = batchIdsStr.split(",");
                Long commentUserId = null;
                
                if ("comment".equals(businessType)) {
                    for (String idStr : ids) {
                        idStr = idStr.trim();
                        if (!idStr.isEmpty()) {
                            Long commentId = Long.parseLong(idStr);
                            Comments comment = commentsService.getById(commentId);
                            if (comment == null) {
                                throw new BusinessException("评论ID不存在: " + commentId);
                            }
                            if (comment.getUserId() == null) {
                                throw new BusinessException("评论ID未关联用户: " + commentId);
                            }
                            if (commentUserId != null && !commentUserId.equals(comment.getUserId())) {
                                throw new BusinessException("批量删除的评论属于不同用户");
                            }
                            commentUserId = comment.getUserId();
                        }
                    }
                    logger.info("从方法参数获取批量评论用户ID: %d", commentUserId);
                    return commentUserId;
                } else if ("article".equals(businessType)) {
                    for (String idStr : ids) {
                        idStr = idStr.trim();
                        if (!idStr.isEmpty()) {
                            Long articleId = Long.parseLong(idStr);
                            Article article = articleService.getById(articleId);
                            if (article == null) {
                                throw new BusinessException("文章ID不存在: " + articleId);
                            }
                            if (article.getUserId() == null) {
                                throw new BusinessException("文章ID未关联用户: " + articleId);
                            }
                            if (commentUserId != null && !commentUserId.equals(article.getUserId())) {
                                throw new BusinessException("批量删除的文章属于不同用户");
                            }
                            commentUserId = article.getUserId();
                        }
                    }
                    logger.info("从方法参数获取批量文章用户ID: %d", commentUserId);
                    return commentUserId;
                }
            }
            
        } catch (Exception e) {
            logger.warning("获取路径多个参数失败: " + e.getMessage());
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

            // 如果找不到参数名，尝试从第一个对象获取
            if (args.length > 0) {
                return extractUserIdFromObject(args[0], paramName, businessType);
            }
        } catch (Exception e) {
            logger.warning("获取请求体参数失败: " + e.getMessage());
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
            // 首先尝试直接获取id属性
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

            // 尝试获取username，然后查询用户ID
            Method usernameMethod = tryGetMethod(obj, "getUsername");
            if (usernameMethod != null) {
                String username = (String) usernameMethod.invoke(obj);
                if (username != null) {
                    User user = userService.findByUsername(username);
                    if (user != null) {
                        logger.info("通过用户名 %s 获取用户ID: %d", username, user.getId());
                        return user.getId();
                    }
                }
            }

            // 尝试获取userId
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
            logger.warning("从对象中提取用户ID失败: " + e.getMessage());
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
            logger.warning("目标资源ID为空，无法检查所有权");
            return false;
        }

        if ("user".equals(businessType)) {
            // 用户只能操作自己
            return currentUserId.equals(targetResourceId);
        } else if ("article".equals(businessType)) {
            // 检查文章所有者
            Article article = articleService.getById(targetResourceId);
            if (article != null) {
                return currentUserId.equals(article.getUserId());
            }
        } else if ("comment".equals(businessType)) {
            // 检查评论所有者
            Comments comment = commentsService.getById(targetResourceId);
            if (comment != null) {
                return currentUserId.equals(comment.getUserId());
            }
        } else if ("category".equals(businessType) || "subcategory".equals(businessType)) {
            // 分类操作不允许自己操作，只有管理员
            return false;
        }

        return false;
    }

    /**
     * 获取方法参数名
     */
    private String[] getParameterNames(ProceedingJoinPoint joinPoint) {
        try {
            MethodSignature methodSignature = (MethodSignature) joinPoint.getSignature();
            Method method = methodSignature.getMethod();

            String[] parameterNames = parameterNameDiscoverer.getParameterNames(method);

            if (parameterNames != null) {
                return parameterNames;
            }

            logger.warning("无法获取方法参数名");
            return new String[] {};

        } catch (Exception e) {
            logger.warning("获取参数名失败: " + e.getMessage());
            return new String[] {};
        }
    }
}

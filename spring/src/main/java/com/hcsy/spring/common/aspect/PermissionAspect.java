package com.hcsy.spring.common.aspect;

import com.hcsy.spring.api.service.CommentsService;
import com.hcsy.spring.api.service.UserService;
import com.hcsy.spring.common.annotation.RequirePermission;
import com.hcsy.spring.common.utils.SimpleLogger;
import com.hcsy.spring.common.utils.UserContext;
import com.hcsy.spring.entity.po.Comments;
import com.hcsy.spring.entity.po.User;

import jakarta.servlet.http.HttpServletRequest;
import lombok.RequiredArgsConstructor;
import org.aspectj.lang.ProceedingJoinPoint;
import org.aspectj.lang.annotation.Around;
import org.aspectj.lang.annotation.Aspect;
import org.aspectj.lang.reflect.MethodSignature;
import org.springframework.core.DefaultParameterNameDiscoverer;
import org.springframework.core.ParameterNameDiscoverer;
import org.springframework.stereotype.Component;
import org.springframework.web.context.request.RequestContextHolder;
import org.springframework.web.context.request.ServletRequestAttributes;

import java.lang.reflect.Method;
import java.util.Arrays;

@Aspect
@Component
@RequiredArgsConstructor
public class PermissionAspect {

    private final UserService userService;
    private final CommentsService commentsService;
    private final SimpleLogger logger;
    private final ParameterNameDiscoverer parameterNameDiscoverer = new DefaultParameterNameDiscoverer();

    @Around("@annotation(requirePermission)")
    public Object checkPermission(ProceedingJoinPoint joinPoint, RequirePermission requirePermission) throws Throwable {
        Long currentUserId = UserContext.getUserId();
        if (currentUserId == null) {
            logger.warning("用户未登录，无法执行权限检查");
            throw new RuntimeException("用户未登录");
        }

        // 获取当前用户信息
        User currentUser = userService.getById(currentUserId);
        if (currentUser == null) {
            throw new RuntimeException("用户不存在");
        }

        String currentUserRole = currentUser.getRole();

        // 检查是否有管理员权限
        boolean hasAdminRole = Arrays.asList(requirePermission.roles()).contains(currentUserRole);

        if (hasAdminRole) {
            // 有管理员权限，直接通过
            return joinPoint.proceed();
        }

        // 如果允许操作自己的数据，检查是否是操作自己
        if (requirePermission.allowSelf()) {
            logger.info("允许操作自己的数据，检查目标用户ID");
            Long targetUserId = getTargetUserId(joinPoint, requirePermission.targetUserIdParam());
            logger.info("当前用户ID: %d, 目标用户ID: %d", currentUserId, targetUserId);
            if (targetUserId != null && targetUserId.equals(currentUserId)) {
                return joinPoint.proceed();
            }
        }

        throw new RuntimeException("权限不足，无法执行此操作");
    }

    private Long getTargetUserId(ProceedingJoinPoint joinPoint, String paramName) {
        try {
            // 从路径参数获取
            ServletRequestAttributes attributes = (ServletRequestAttributes) RequestContextHolder
                    .getRequestAttributes();
            if (attributes != null) {
                HttpServletRequest request = attributes.getRequest();
                String pathVariable = request.getRequestURI();
                // 排除查询参数
                if (request.getQueryString() != null) {
                    pathVariable = pathVariable.split("\\?")[0];
                }
                // 简单的路径解析，你可能需要更复杂的逻辑
                String[] parts = pathVariable.split("/");
                for (int i = 0; i < parts.length; i++) {
                    // 目前路径一定是/users/status/{id}
                    if (parts[i].equals("status") && i + 1 < parts.length) {
                        try {
                            logger.info(pathVariable + " 中的参数: " + parts[i + 1]);
                            return Long.parseLong(parts[i + 1]);
                        } catch (NumberFormatException e) {
                            continue;
                        }
                    }
                    // 获取请求的方法，如果是DELETE 就进入if执行对应逻辑
                    else if (parts[i].equals("comments") && request.getMethod().equals("DELETE")) {
                        try {
                            String nextPart = parts[i + 1];
                            if (nextPart.equals("batch")) {
                                // 批量删除，取第一个ID
                                String idsPart = parts[i + 2];
                                String[] ids = idsPart.split(",");
                                logger.info(pathVariable + " 中的参数: " + ids[0]);
                                // 通过id数组获取对应评论的用户ID，如果出现不同就返回空，否则返回对应的用户ID
                                Long commentUserId = null;
                                for (String idStr : ids) {
                                    Long commentId = Long.parseLong(idStr);
                                    Comments comment = commentsService.getById(commentId);
                                    if (comment == null) {
                                        logger.warning("评论ID不存在: " + commentId);
                                        throw new RuntimeException("评论ID不存在: " + commentId);
                                    }
                                    if (comment.getUserId() == null) {
                                        logger.warning("评论ID未关联用户: " + commentId);
                                        throw new RuntimeException("评论ID未关联用户: " + commentId);
                                    }
                                    if (commentUserId != null
                                            && commentUserId.longValue() != comment.getUserId().longValue()) {
                                        logger.warning("批量删除的评论属于不同用户，无法确定目标用户ID");
                                        return null;
                                    }
                                    commentUserId = comment.getUserId();
                                }
                                return commentUserId;
                            } else {
                                // 单个删除
                                logger.info(pathVariable + " 中的参数: " + nextPart);
                                Long commentId = Long.parseLong(nextPart);
                                Comments comment = commentsService.getById(commentId);
                                if (comment == null) {
                                    logger.warning("评论ID不存在: " + commentId);
                                    throw new RuntimeException("评论ID不存在: " + commentId);
                                }
                                if (comment.getUserId() == null) {
                                    logger.warning("评论ID未关联用户: " + commentId);
                                    throw new RuntimeException("评论ID未关联用户: " + commentId);
                                }
                                return comment.getUserId();
                            }
                        } catch (Exception e) {
                            continue;
                        }
                    }
                }
            }

            // 从方法参数获取
            Object[] args = joinPoint.getArgs();
            String[] paramNames = getParameterNames(joinPoint);
            for (int i = 0; i < paramNames.length; i++) {
                // paramName = "userDto";
                if (paramName.equals(paramNames[i])) {
                    // 两种情况，用户DTO直接获取id，其他DTO获取对应的username，再获取对应的用户ID
                    if (paramName.equals("userDto")) {
                        // 正常只会有1个DTO参数
                        return ((Integer) args[0].getClass().getMethod("getId").invoke(args[0])).longValue();
                    } else {
                        // 其他DTO，获取username，再查询用户ID
                        String username = (String) args[0].getClass().getMethod("getUsername").invoke(args[0]);
                        User user = userService.findByUsername(username);
                        if (user != null) {
                            return user.getId();
                        } else {
                            logger.warning("通过用户名未找到对应的用户: " + username);
                            throw new RuntimeException("通过用户名未找到对应的用户: " + username);
                        }
                    }

                }
            }
        } catch (Exception e) {
            logger.warning("获取目标用户ID失败", e);
            throw new RuntimeException("获取目标用户ID失败");
        }
        return null;
    }

    private String[] getParameterNames(ProceedingJoinPoint joinPoint) {
        try {
            MethodSignature methodSignature = (MethodSignature) joinPoint.getSignature();
            Method method = methodSignature.getMethod();

            // 使用Spring的ParameterNameDiscoverer获取参数名
            String[] parameterNames = parameterNameDiscoverer.getParameterNames(method);

            if (parameterNames != null) {
                return parameterNames;
            }

            // 如果无法获取参数名，返回默认值
            logger.warning("无法获取方法参数名，使用默认参数名");
            return new String[] { "id", "userDto" };

        } catch (Exception e) {
            logger.warning("获取参数名失败", e);
            // 简化处理，返回默认参数名
            return new String[] { "id", "userDto" };
        }
    }
}
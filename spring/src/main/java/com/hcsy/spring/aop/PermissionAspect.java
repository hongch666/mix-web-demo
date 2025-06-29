package com.hcsy.spring.aop;

import com.hcsy.spring.annotation.RequirePermission;
import com.hcsy.spring.po.User;
import com.hcsy.spring.service.UserService;
import com.hcsy.spring.utils.SimpleLogger;
import com.hcsy.spring.utils.UserContext;

import jakarta.servlet.http.HttpServletRequest;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.aspectj.lang.ProceedingJoinPoint;
import org.aspectj.lang.annotation.Around;
import org.aspectj.lang.annotation.Aspect;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;
import org.springframework.web.context.request.RequestContextHolder;
import org.springframework.web.context.request.ServletRequestAttributes;

import java.util.Arrays;

@Aspect
@Component
@RequiredArgsConstructor
@Slf4j
public class PermissionAspect {

    @Autowired
    private UserService userService;
    private final SimpleLogger logger;

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
            logger.info("当前用户ID: {}, 目标用户ID: {}", currentUserId, targetUserId);
            if (targetUserId != null && targetUserId.equals(currentUserId)) {
                return joinPoint.proceed();
            }
        }

        throw new RuntimeException("权限不足，无法执行此操作");
    }

    private Long getTargetUserId(ProceedingJoinPoint joinPoint, String paramName) {
        System.out.println("我是测试！！！！！！！！");
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
                            // 继续查找
                        }
                    }
                }
            }

            // 从方法参数获取
            Object[] args = joinPoint.getArgs();
            String[] paramNames = getParameterNames(joinPoint);
            for (int i = 0; i < paramNames.length; i++) {
                paramName = "userDto";
                if (paramName.equals(paramNames[i])) {
                    // 正常只会有1个DTO参数
                    return ((Integer) args[0].getClass().getMethod("getId").invoke(args[0])).longValue();
                }
            }
        } catch (Exception e) {
            logger.warning("获取目标用户ID失败", e);
            throw new RuntimeException("获取目标用户ID失败");
        }
        return null;
    }

    private String[] getParameterNames(ProceedingJoinPoint joinPoint) {
        // 这里需要使用反射获取参数名，或者使用Spring的ParameterNameDiscoverer
        // 简化处理，返回默认参数名
        return new String[] { "id", "userDto" };
    }
}
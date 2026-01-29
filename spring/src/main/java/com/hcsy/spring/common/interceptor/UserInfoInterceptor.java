package com.hcsy.spring.common.interceptor;

import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;

import org.springframework.stereotype.Component;
import org.springframework.web.servlet.HandlerInterceptor;

import com.hcsy.spring.common.utils.Constants;
import com.hcsy.spring.common.utils.SimpleLogger;
import com.hcsy.spring.common.utils.UserContext;

import org.springframework.lang.Nullable;

@Component
@RequiredArgsConstructor
public class UserInfoInterceptor implements HandlerInterceptor {

    private final SimpleLogger logger;

    @SuppressWarnings("null")
    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) {
        String userIdStr = request.getHeader("X-User-Id");
        String username = request.getHeader("X-Username");
        String authHeader = request.getHeader("Authorization");

        if (userIdStr != null) {
            try {
                Long userId = Long.parseLong(userIdStr);
                UserContext.setUserId(userId);
                UserContext.setUsername(username);
            } catch (NumberFormatException e) {
                // 如果格式错误，可以记录日志，也可以拦截请求
                logger.error(Constants.USER_INTERCEPTOR + userIdStr);
            }
        }

        // 从 Authorization header 中提取 token 并存储到 ThreadLocal
        if (authHeader != null && authHeader.startsWith("Bearer ")) {
            String token = authHeader.substring(7); // 移除 "Bearer " 前缀
            UserContext.setToken(token);
        }

        return true;
    }

    @SuppressWarnings("null")
    @Override
    public void afterCompletion(HttpServletRequest request, HttpServletResponse response, Object handler,
            @Nullable Exception ex) {
        UserContext.clear(); // 防止线程复用造成用户信息泄露
    }
}

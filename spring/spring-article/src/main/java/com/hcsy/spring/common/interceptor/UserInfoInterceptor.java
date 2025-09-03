package com.hcsy.spring.common.interceptor;

import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.stereotype.Component;
import org.springframework.web.servlet.HandlerInterceptor;

import com.hcsy.spring.common.utils.UserContext;

import org.springframework.lang.Nullable;

@Component
public class UserInfoInterceptor implements HandlerInterceptor {

    @SuppressWarnings("null")
    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) {
        String userIdStr = request.getHeader("X-User-Id");
        String username = request.getHeader("X-Username");

        if (userIdStr != null) {
            try {
                Long userId = Long.parseLong(userIdStr);
                UserContext.setUserId(userId);
                UserContext.setUsername(username);
            } catch (NumberFormatException e) {
                // 如果格式错误，可以记录日志，也可以拦截请求
                System.err.println("Invalid userId in header: " + userIdStr);
            }
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

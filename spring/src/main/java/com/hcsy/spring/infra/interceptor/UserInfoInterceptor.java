package com.hcsy.spring.infra.interceptor;

import org.springframework.lang.Nullable;
import org.springframework.stereotype.Component;
import org.springframework.web.servlet.HandlerInterceptor;

import com.hcsy.spring.common.utils.Constants;
import com.hcsy.spring.common.utils.SimpleLogger;
import com.hcsy.spring.common.utils.UserContext;

import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;

@Component
@RequiredArgsConstructor
public class UserInfoInterceptor implements HandlerInterceptor {

    private final SimpleLogger logger;

    @SuppressWarnings("null")
    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) {
        String userIdStr = request.getHeader("X-User-Id");
        String username = request.getHeader("X-Username");
        String sessionId = request.getHeader("X-Session-Id");
        String authHeader = request.getHeader("Authorization");

        if (userIdStr != null) {
            try {
                Long userId = Long.parseLong(userIdStr);
                UserContext.setUserId(userId);
                UserContext.setUsername(username);
            } catch (NumberFormatException e) {
                logger.error(Constants.USER_INTERCEPTOR + userIdStr);
            }
        }

        if (sessionId != null) {
            UserContext.setSessionId(sessionId);
        }

        if (authHeader != null && authHeader.startsWith("Bearer ")) {
            String token = authHeader.substring(7);
            UserContext.setToken(token);
        }

        return true;
    }

    @SuppressWarnings("null")
    @Override
    public void afterCompletion(HttpServletRequest request, HttpServletResponse response, Object handler,
            @Nullable Exception ex) {
        UserContext.clear();
    }
}

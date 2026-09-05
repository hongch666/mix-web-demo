package com.hcsy.spring.infra.filter;

import org.springframework.http.server.reactive.ServerHttpRequest;
import org.springframework.stereotype.Component;
import org.springframework.web.server.ServerWebExchange;
import org.springframework.web.server.WebFilter;
import org.springframework.web.server.WebFilterChain;

import com.hcsy.spring.common.constants.HeaderNames;
import com.hcsy.spring.common.utils.UserContext;

import reactor.core.publisher.Mono;

/**
 * 用户上下文 WebFilter（WebFlux 响应式实现）
 * 从请求头解析用户信息并写入 Reactor Context
 * 替代原有的 UserInfoInterceptor + WebConfig（Servlet MVC 时代的拦截器 + 配置类）
 */
@Component
public class UserContextWebFilter implements WebFilter {

    @Override
    public Mono<Void> filter(ServerWebExchange exchange, WebFilterChain chain) {
        ServerHttpRequest request = exchange.getRequest();
        Long userId = parseLong(request.getHeaders().getFirst(HeaderNames.USER_ID));
        String username = request.getHeaders().getFirst(HeaderNames.USERNAME);
        String sessionId = request.getHeaders().getFirst(HeaderNames.SESSION_ID);
        String token = extractToken(request.getHeaders().getFirst("Authorization"));
        String internalToken = extractToken(request.getHeaders().getFirst("X-Internal-Token"));

        return chain.filter(exchange)
            .contextWrite(ctx -> UserContext.writeContext(ctx, userId, username, sessionId, token, internalToken));
    }

    private Long parseLong(String value) {
        if (value == null)
            return null;
        try {
            return Long.parseLong(value);
        } catch (NumberFormatException e) {
            return null;
        }
    }

    private String extractToken(String authHeader) {
        if (authHeader != null && authHeader.startsWith("Bearer ")) {
            return authHeader.substring(7);
        }
        return null;
    }
}

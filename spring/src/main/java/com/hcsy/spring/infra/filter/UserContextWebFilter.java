package com.hcsy.spring.infra.filter;

import org.springframework.http.server.reactive.ServerHttpRequest;
import org.springframework.stereotype.Component;
import org.springframework.web.server.ServerWebExchange;
import org.springframework.web.server.WebFilter;
import org.springframework.web.server.WebFilterChain;

import com.hcsy.spring.common.utils.UserContext;

import reactor.core.publisher.Mono;

/**
 * 用户上下文 WebFilter
 * 替代原有的 UserInfoInterceptor + WebConfig
 * 将请求用户信息写入 Reactor Context
 */
@Component
public class UserContextWebFilter implements WebFilter {

    @SuppressWarnings("null")
    @Override
    public Mono<Void> filter(ServerWebExchange exchange, WebFilterChain chain) {
        ServerHttpRequest request = exchange.getRequest();
        Long userId = parseLong(request.getHeaders().getFirst("X-User-Id"));
        String username = request.getHeaders().getFirst("X-Username");
        String sessionId = request.getHeaders().getFirst("X-Session-Id");
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

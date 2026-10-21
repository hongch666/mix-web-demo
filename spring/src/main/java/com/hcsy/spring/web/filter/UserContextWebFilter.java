package com.hcsy.spring.web.filter;

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

    /**
     * WebFilter入口，从请求头解析用户ID、用户名、会话ID与令牌并写入Reactor上下文，供下游响应式链路读取当前用户信息
     */
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

    /**
     * 将字符串安全地解析为Long，空值或格式非法时返回null
     */
    private Long parseLong(String value) {
        if (value == null)
            return null;
        try {
            return Long.parseLong(value);
        } catch (NumberFormatException e) {
            return null;
        }
    }

    /**
     * 从 Authorization 或内部令牌请求头中剥离 Bearer 前缀提取令牌原文
     */
    private String extractToken(String authHeader) {
        if (authHeader != null && authHeader.startsWith("Bearer ")) {
            return authHeader.substring(7);
        }
        return null;
    }
}

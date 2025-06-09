package com.hcsy.gateway.filter;

import com.hcsy.gateway.utils.JwtUtil;
import lombok.RequiredArgsConstructor;
import org.springframework.cloud.gateway.filter.GatewayFilterChain;
import org.springframework.cloud.gateway.filter.GlobalFilter;
import org.springframework.core.Ordered;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.server.reactive.ServerHttpRequest;
import org.springframework.http.server.reactive.ServerHttpResponse;
import org.springframework.stereotype.Component;
import org.springframework.util.AntPathMatcher;
import org.springframework.util.CollectionUtils;
import org.springframework.web.server.ServerWebExchange;
import reactor.core.publisher.Mono;
import reactor.core.scheduler.Schedulers;

import java.util.List;

@Component
@RequiredArgsConstructor
public class AuthGlobalFilter implements GlobalFilter, Ordered {

    private final JwtUtil jwtUtil;
    private final AntPathMatcher antPathMatcher = new AntPathMatcher();

    // 需要排除的路径（建议通过配置中心管理）
    private static final List<String> EXCLUDE_PATHS = List.of(
            "/users/login",
            "/auth/register",
            "/public/**",
            "/actuator/**",
            "/v3/api-docs/**",
            "/swagger-ui/**",
            "/swagger-resources/**");

    @Override
    public Mono<Void> filter(ServerWebExchange exchange, GatewayFilterChain chain) {
        ServerHttpRequest request = exchange.getRequest();
        String path = request.getPath().toString();

        // 1. 排除不需要认证的路径
        if (isExcludePath(path)) {
            return chain.filter(exchange);
        }

        // 2. 获取并验证Token
        String token = extractToken(request);
        if (token == null) {
            return unauthorizedResponse(exchange, "Missing authorization token");
        }

        try {
            if (!jwtUtil.validateToken(token)) {
                return unauthorizedResponse(exchange, "Invalid token");
            }

            // 3. 传递用户信息到下游服务
            Long userId = jwtUtil.extractUserId(token);
            String username = jwtUtil.extractUsername(token);

            ServerHttpRequest mutatedRequest = request.mutate()
                    .header("X-User-Id", userId.toString())
                    .header("X-Username", username)
                    .build();

            // 4. 记录审计日志（异步）
            logAccess(userId, path);

            return chain.filter(exchange.mutate().request(mutatedRequest).build());

        } catch (Exception ex) {
            return unauthorizedResponse(exchange, "Token verification failed: " + ex.getMessage());
        }
    }

    private String extractToken(ServerHttpRequest request) {
        List<String> headers = request.getHeaders().get(HttpHeaders.AUTHORIZATION);
        if (CollectionUtils.isEmpty(headers)) {
            return null;
        }

        // 支持 Bearer Token 和直接Token两种形式
        String authHeader = headers.get(0);
        if (authHeader.startsWith("Bearer ")) {
            return authHeader.substring(7);
        }
        return authHeader;
    }

    private boolean isExcludePath(String path) {
        return EXCLUDE_PATHS.stream().anyMatch(pattern -> antPathMatcher.match(pattern, path));
    }

    private Mono<Void> unauthorizedResponse(ServerWebExchange exchange, String message) {
        ServerHttpResponse response = exchange.getResponse();
        response.setStatusCode(HttpStatus.UNAUTHORIZED);
        response.getHeaders().add("X-Error-Message", message);
        return response.setComplete();
    }

    private void logAccess(Long userId, String path) {
        // 异步记录访问日志（实际项目可接入ELK等日志系统）
        Mono.fromRunnable(() -> System.out.printf("[AUDIT] User %d accessed %s at %d%n",
                userId, path, System.currentTimeMillis())).subscribeOn(Schedulers.boundedElastic()).subscribe();
    }

    @Override
    public int getOrder() {
        return -100; // 确保在其它全局过滤器之前执行
    }
}
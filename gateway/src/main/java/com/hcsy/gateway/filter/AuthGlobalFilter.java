package com.hcsy.gateway.filter;

import com.hcsy.gateway.utils.JwtUtil;
import com.hcsy.gateway.utils.RedisUtil;
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
    private final RedisUtil redisUtil;
    private final AntPathMatcher antPathMatcher = new AntPathMatcher();

    // 需要排除的路径（建议通过配置中心管理）
    private static final List<String> EXCLUDE_PATHS = List.of(
            "/users/login",
            "/users/register",
            "/static/**",
            "/upload/**",
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
            // 3. 基础验证：Token签名和过期时间
            if (!jwtUtil.validateToken(token)) {
                return unauthorizedResponse(exchange, "Invalid or expired token");
            }

            // 4. 从 Token 中提取用户 ID
            Long userId = jwtUtil.extractUserId(token);

            // 5. ✨ 核心检验：Token 是否在 Redis 列表中（检查是否被管理员踢下线）
            String tokenListKey = "user:tokens:" + userId;
            if (!redisUtil.existsInList(tokenListKey, token)) {
                return unauthorizedResponse(exchange, "Token has been revoked or user logged out");
            }

            // 6. 检查用户状态
            String userStatus = redisUtil.get("user:status:" + userId);
            if ("0".equals(userStatus)) {
                return unauthorizedResponse(exchange, "User is offline");
            }

            // 7. 传递用户信息和 Token 到下游服务
            String username = jwtUtil.extractUsername(token);

            ServerHttpRequest mutatedRequest = request.mutate()
                    .header("X-User-Id", userId.toString())
                    .header("X-Username", username)
                    .header("Authorization", "Bearer " + token)
                    .build();

            // 8. 记录审计日志（异步）
            logAccess(userId, path);

            return chain.filter(exchange.mutate().request(mutatedRequest).build());

        } catch (Exception ex) {
            return unauthorizedResponse(exchange, "Token verification failed: " + ex.getMessage());
        }
    }

    private String extractToken(ServerHttpRequest request) {
        // 首先尝试从 Authorization header 获取
        List<String> headers = request.getHeaders().get(HttpHeaders.AUTHORIZATION);
        if (!CollectionUtils.isEmpty(headers)) {
            @SuppressWarnings("null")
            String authHeader = headers.get(0);
            if (authHeader.startsWith("Bearer ")) {
                return authHeader.substring(7);
            }
            return authHeader;
        }

        // 如果 Authorization header 没有，尝试从 query parameter 获取 (WebSocket 场景)
        if (request.getQueryParams() != null) {
            String tokenFromQuery = request.getQueryParams().getFirst("token");
            if (tokenFromQuery != null && !tokenFromQuery.trim().isEmpty()) {
                return tokenFromQuery;
            }
        }

        return null;
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
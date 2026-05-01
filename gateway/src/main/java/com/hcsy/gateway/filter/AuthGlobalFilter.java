package com.hcsy.gateway.filter;

import java.util.List;

import org.springframework.cloud.gateway.filter.GatewayFilterChain;
import org.springframework.cloud.gateway.filter.GlobalFilter;
import org.springframework.core.Ordered;
import org.springframework.http.HttpHeaders;
import org.springframework.http.server.reactive.ServerHttpRequest;
import org.springframework.http.server.reactive.ServerHttpResponse;
import org.springframework.stereotype.Component;
import org.springframework.util.AntPathMatcher;
import org.springframework.util.CollectionUtils;
import org.springframework.web.server.ServerWebExchange;

import com.hcsy.gateway.common.BusinessException;
import com.hcsy.gateway.common.Constants;
import com.hcsy.gateway.common.HttpCode;
import com.hcsy.gateway.common.Result;
import com.hcsy.gateway.config.AuthProperties;
import com.hcsy.gateway.utils.JwtUtil;
import com.hcsy.gateway.utils.RedisUtil;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import reactor.core.publisher.Mono;
import reactor.core.scheduler.Schedulers;

@Component
@RequiredArgsConstructor
@Slf4j
public class AuthGlobalFilter implements GlobalFilter, Ordered {

    private final JwtUtil jwtUtil;
    private final RedisUtil redisUtil;
    private final AuthProperties authProperties;
    private final AntPathMatcher antPathMatcher = new AntPathMatcher();

    @Override
    public Mono<Void> filter(ServerWebExchange exchange, GatewayFilterChain chain) {
        ServerHttpRequest request = exchange.getRequest();
        String path = request.getPath().toString();

        // 1. 排除不需要认证的路径
        if (isExcludePath(path)) {
            log.info("排除身份验证的路径: {}", path);
            return chain.filter(exchange);
        }

        // 2. 获取并验证Token
        String token = extractToken(request);
        if (token == null) {
            return errorResponse(exchange, HttpCode.UNAUTHORIZED, "用户未登录，请先登录", Constants.USER_NOT_LOGIN);
        }

        try {
            // 3. 基础验证：Token签名和过期时间
            if (!jwtUtil.validateToken(token)) {
                return errorResponse(exchange, HttpCode.UNAUTHORIZED, "无效的Token", Constants.TOKEN_INVALID);
            }

            // 4. 从 Token 中提取用户 ID
            Long userId = jwtUtil.extractUserId(token);

            // 5. 核心检验：Token 是否在 Redis 列表中（检查是否被管理员踢下线）
            String tokenListKey = "user:tokens:" + userId;
            if (!redisUtil.existsInList(tokenListKey, token)) {
                return errorResponse(exchange, HttpCode.UNAUTHORIZED, "用户未登录，请先登录", Constants.USER_NOT_LOGIN);
            }

            // 6. 检查用户状态
            String userStatus = redisUtil.get("user:status:" + userId);
            if ("0".equals(userStatus)) {
                return errorResponse(exchange, HttpCode.UNAUTHORIZED, "用户未登录，请先登录", Constants.USER_NOT_LOGIN);
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
            log.info("身份验证成功 - 用户ID: {}, 路径: {}", userId, path);

            return chain.filter(exchange.mutate().request(mutatedRequest).build());

        } catch (BusinessException ex) {
            // JwtUtil 抛出的 BusinessException，携带具体错误标识
            log.error("[{}] 认证失败 - 路径: {}", ex.getError(), path, ex);
            return errorResponse(exchange, ex.getStatusCode(), ex.getMessage(), ex.getError());
        } catch (Exception ex) {
            log.error("认证异常 - 路径: {}", path, ex);
            return errorResponse(exchange, HttpCode.UNAUTHORIZED, "无效的Token", Constants.TOKEN_INVALID);
        }
    }

    private String extractToken(ServerHttpRequest request) {
        List<String> headers = request.getHeaders().get(HttpHeaders.AUTHORIZATION);
        if (!CollectionUtils.isEmpty(headers)) {
            @SuppressWarnings("null")
            String authHeader = headers.get(0);
            if (authHeader.startsWith("Bearer ")) {
                return authHeader.substring(7);
            }
            return authHeader;
        }

        if (request.getQueryParams() != null) {
            String tokenFromQuery = request.getQueryParams().getFirst("token");
            if (tokenFromQuery != null && !tokenFromQuery.trim().isEmpty()) {
                return tokenFromQuery;
            }
        }

        return null;
    }

    @SuppressWarnings("null")
    private boolean isExcludePath(String path) {
        return authProperties.getExcludePaths().stream()
                .anyMatch(pattern -> antPathMatcher.match(pattern, path));
    }

    private Mono<Void> errorResponse(ServerWebExchange exchange, int code, String msg, String errorIdentifier) {
        ServerHttpResponse response = exchange.getResponse();
        response.setStatusCode(org.springframework.http.HttpStatus.valueOf(code));
        log.error("[{}] {}", errorIdentifier, msg);
        return Result.error(code, msg).writeTo(response);
    }

    private void logAccess(Long userId, String path) {
        Mono.fromRunnable(() -> log.info("[AUDIT] User {} accessed {} at {}", userId, path, System.currentTimeMillis()))
                .subscribeOn(Schedulers.boundedElastic()).subscribe();
    }

    @Override
    public int getOrder() {
        return -100;
    }
}

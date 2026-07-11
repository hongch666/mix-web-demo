package com.hcsy.gateway.filter;

import java.util.List;

import org.springframework.cloud.gateway.filter.GatewayFilterChain;
import org.springframework.cloud.gateway.filter.GlobalFilter;
import org.springframework.core.Ordered;
import org.springframework.dao.DataAccessException;
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

        // 2. 获取 access token（只接受 access token）
        String token = extractToken(request);
        if (token == null) {
            return errorResponse(exchange, HttpCode.UNAUTHORIZED, "用户未登录，请先登录", Constants.USER_NOT_LOGIN);
        }

        try {
            // 3. 校验 JWT 签名、过期时间和 tokenType=access
            jwtUtil.validateAccessToken(token);

            // 4. 提取 userId、username、sessionId
            Long userId = jwtUtil.extractUserId(token);
            String username = jwtUtil.extractUsername(token);
            String sessionId = jwtUtil.extractSessionId(token);

            // 5. 判断 user:access:{accessToken} 是否存在且值正确
            String accessKey = "user:access:" + token;
            String storedValue = redisUtil.get(accessKey);
            String expectedValue = userId + ":" + sessionId;
            if (storedValue == null || !expectedValue.equals(storedValue)) {
                return errorResponse(exchange, HttpCode.UNAUTHORIZED, "用户未登录，请先登录", Constants.USER_NOT_LOGIN);
            }

            // 6. 判断 user:session:{userId}:{sessionId} 是否存在
            String sessionKey = "user:session:" + userId + ":" + sessionId;
            if (!redisUtil.exists(sessionKey)) {
                return errorResponse(exchange, HttpCode.UNAUTHORIZED, "用户未登录，请先登录", Constants.USER_NOT_LOGIN);
            }

            // 7. 校验 session hash 中保存的 accessToken 与请求 token 一致
            String storedAccessToken = redisUtil.getHash(sessionKey, "accessToken");
            if (!token.equals(storedAccessToken)) {
                return errorResponse(exchange, HttpCode.UNAUTHORIZED, "用户未登录，请先登录", Constants.USER_NOT_LOGIN);
            }

            // 8. 校验 user:status:{userId} 不为 0
            String userStatus = redisUtil.get("user:status:" + userId);
            if ("0".equals(userStatus)) {
                return errorResponse(exchange, HttpCode.UNAUTHORIZED, "用户未登录，请先登录", Constants.USER_NOT_LOGIN);
            }

            // 9. 传递用户信息到下游服务
            ServerHttpRequest mutatedRequest = request.mutate()
                    .header("X-User-Id", userId.toString())
                    .header("X-Username", username)
                    .header("X-Session-Id", sessionId)
                    .header("Authorization", "Bearer " + token)
                    .build();

            // 10. 记录审计日志（异步）
            logAccess(userId, path);
            log.info("身份验证成功 - 用户ID: {}, 路径: {}", userId, path);

            return chain.filter(exchange.mutate().request(mutatedRequest).build());

        } catch (BusinessException ex) {
            log.error("[{}] 认证失败 - 路径: {}", ex.getError(), path, ex);
            return errorResponse(exchange, ex.getStatusCode(), ex.getMessage(), ex.getError());
        } catch (DataAccessException ex) {
            // Redis 不可用（连接断开、超时、重启中等），不应判定为用户未登录
            log.error("[{}] Redis 不可用，认证流程中断 - 路径: {}", Constants.REDIS_UNAVAILABLE, path, ex);
            return errorResponse(exchange, HttpCode.SERVICE_UNAVAILABLE, "服务暂时不可用，请稍后重试", Constants.REDIS_UNAVAILABLE);
        } catch (Exception ex) {
            // 认证流程中出现的其他非预期异常，不应返回 401 误导前端退出登录
            log.error("[{}] 认证流程非预期异常 - 路径: {}", Constants.AUTH_UNEXPECTED_ERROR, path, ex);
            return errorResponse(exchange, HttpCode.INTERNAL_SERVER_ERROR, "服务器内部错误，请稍后重试", Constants.AUTH_UNEXPECTED_ERROR);
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

package com.hcsy.gateway.filter;

import org.springframework.cloud.gateway.filter.GatewayFilterChain;
import org.springframework.cloud.gateway.filter.GlobalFilter;
import org.springframework.core.Ordered;
import org.springframework.http.server.reactive.ServerHttpResponse;
import org.springframework.stereotype.Component;
import org.springframework.util.AntPathMatcher;
import org.springframework.web.server.ServerWebExchange;

import com.hcsy.gateway.common.Constants;
import com.hcsy.gateway.common.HttpCode;
import com.hcsy.gateway.common.Result;
import com.hcsy.gateway.properties.RateLimitProperties;
import com.hcsy.gateway.utils.TokenBucketRateLimiter;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import reactor.core.publisher.Mono;

/**
 * 限流全局过滤器
 * 优先级设置为2，在认证过滤器（Ordered.HIGHEST_PRECEDENCE）之后执行
 */
@Component
@RequiredArgsConstructor
@Slf4j
public class RateLimitGlobalFilter implements GlobalFilter, Ordered {

    private final RateLimitProperties rateLimitProperties;
    private final TokenBucketRateLimiter tokenBucketRateLimiter;
    private final AntPathMatcher antPathMatcher = new AntPathMatcher();

    @Override
    public Mono<Void> filter(ServerWebExchange exchange, GatewayFilterChain chain) {
        if (!rateLimitProperties.isEnabled()) {
            return chain.filter(exchange);
        }

        String path = exchange.getRequest().getPath().value();
        String clientId = getClientIdentifier(exchange);

        RateLimitProperties.RateLimitPath rateLimitPath = matchRateLimitPath(path);

        if (rateLimitPath == null || !rateLimitPath.getEnabled()) {
            return chain.filter(exchange);
        }

        String rateLimitKey = buildRateLimitKey(path, clientId);

        boolean allowed = tokenBucketRateLimiter.isAllowed(
            rateLimitKey,
            rateLimitPath.getCapacity(),
            rateLimitPath.getRefillRate()
        );

        if (!allowed) {
            log.warn("[{}] 请求被限流: path={}, clientId={}", Constants.RATE_LIMIT_EXCEEDED, path, clientId);
            return rateLimitExceededResponse(exchange, rateLimitPath.getMessage());
        }

        log.debug("限流检查通过: path={}, clientId={}", path, clientId);
        return chain.filter(exchange);
    }

    @SuppressWarnings("null")
    private RateLimitProperties.RateLimitPath matchRateLimitPath(String path) {
        for (String pattern : rateLimitProperties.getPaths().keySet()) {
            if (antPathMatcher.match(pattern, path)) {
                return rateLimitProperties.mergeWithCommon(rateLimitProperties.getPaths().get(pattern));
            }
        }
        return null;
    }

    private String getClientIdentifier(ServerWebExchange exchange) {
        String userId = exchange.getRequest().getHeaders().getFirst("X-User-Id");
        if (userId != null) {
            return "user:" + userId;
        }

        String clientIp = getClientIp(exchange);
        if (clientIp != null) {
            return "ip:" + clientIp;
        }

        return "unknown";
    }

    @SuppressWarnings("null")
    private String getClientIp(ServerWebExchange exchange) {
        String[] headers = {
            "X-Forwarded-For",
            "X-Real-IP",
            "Proxy-Client-IP",
            "WL-Proxy-Client-IP"
        };

        for (String header : headers) {
            String ip = exchange.getRequest().getHeaders().getFirst(header);
            if (ip != null && !ip.isEmpty()) {
                if ("X-Forwarded-For".equals(header)) {
                    ip = ip.split(",")[0];
                }
                return ip;
            }
        }

        if (exchange.getRequest().getRemoteAddress() != null) {
            return exchange.getRequest().getRemoteAddress().getHostName();
        }

        return null;
    }

    private String buildRateLimitKey(String path, String clientId) {
        String cleanPath = path.split("\\?")[0];
        return "rate-limit:" + cleanPath + ":" + clientId;
    }

    private Mono<Void> rateLimitExceededResponse(ServerWebExchange exchange, String message) {
        ServerHttpResponse response = exchange.getResponse();
        response.setStatusCode(org.springframework.http.HttpStatus.TOO_MANY_REQUESTS);
        return Result.error(HttpCode.TOO_MANY_REQUESTS, message).writeTo(response);
    }

    @Override
    public int getOrder() {
        return Ordered.HIGHEST_PRECEDENCE + 2;
    }
}

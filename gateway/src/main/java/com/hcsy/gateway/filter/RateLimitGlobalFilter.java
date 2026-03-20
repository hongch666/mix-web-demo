package com.hcsy.gateway.filter;

import org.springframework.cloud.gateway.filter.GatewayFilterChain;
import org.springframework.cloud.gateway.filter.GlobalFilter;
import org.springframework.core.Ordered;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.util.AntPathMatcher;
import org.springframework.web.server.ServerWebExchange;

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
        // 检查限流是否启用
        if (!rateLimitProperties.isEnabled()) {
            return chain.filter(exchange);
        }

        String path = exchange.getRequest().getPath().value();
        String clientId = getClientIdentifier(exchange);

        // 检查该路径是否需要限流
        RateLimitProperties.RateLimitPath rateLimitPath = matchRateLimitPath(path);

        if (rateLimitPath == null || !rateLimitPath.getEnabled()) {
            // 该路径不需要限流
            return chain.filter(exchange);
        }

        // 构造限流key: rate-limit:{path}:{clientId}
        String rateLimitKey = buildRateLimitKey(path, clientId);

        // 执行限流检查
        boolean allowed = tokenBucketRateLimiter.isAllowed(
            rateLimitKey,
            rateLimitPath.getCapacity(),
            rateLimitPath.getRefillRate()
        );

        if (!allowed) {
            log.warn("请求被限流: path={}, clientId={}", path, clientId);
            return rateLimitExceededResponse(exchange, rateLimitPath.getMessage());
        }

        log.debug("限流检查通过: path={}, clientId={}", path, clientId);
        return chain.filter(exchange);
    }

    /**
     * 匹配该路径是否需要限流
     */
    @SuppressWarnings("null")
    private RateLimitProperties.RateLimitPath matchRateLimitPath(String path) {
        for (String pattern : rateLimitProperties.getPaths().keySet()) {
            if (antPathMatcher.match(pattern, path)) {
                return rateLimitProperties.getPaths().get(pattern);
            }
        }
        return null;
    }

    /**
     * 获取客户端标识符（用于区分不同客户端的限流）
     * 优先级: userId > IP > 默认值
     */
    private String getClientIdentifier(ServerWebExchange exchange) {
        // 首先尝试从请求头获取用户ID (认证过滤器放入)
        String userId = exchange.getRequest().getHeaders().getFirst("X-User-Id");
        if (userId != null) {
            return "user:" + userId;
        }

        // 其次获取客户端IP
        String clientIp = getClientIp(exchange);
        if (clientIp != null) {
            return "ip:" + clientIp;
        }

        // 最后使用默认值
        return "unknown";
    }

    /**
     * 获取客户端真实IP地址
     */
    @SuppressWarnings("null")
    private String getClientIp(ServerWebExchange exchange) {
        // 尝试多个可能的IP头
        String[] headers = {
            "X-Forwarded-For",
            "X-Real-IP",
            "Proxy-Client-IP",
            "WL-Proxy-Client-IP"
        };

        for (String header : headers) {
            String ip = exchange.getRequest().getHeaders().getFirst(header);
            if (ip != null && !ip.isEmpty()) {
                // X-Forwarded-For 可能包含多个IP，取第一个
                if ("X-Forwarded-For".equals(header)) {
                    ip = ip.split(",")[0];
                }
                return ip;
            }
        }

        // 从远程地址获取IP
        if (exchange.getRequest().getRemoteAddress() != null) {
            return exchange.getRequest().getRemoteAddress().getHostName();
        }

        return null;
    }

    /**
     * 构造限流key
     */
    private String buildRateLimitKey(String path, String clientId) {
        // 去掉路径中的query参数
        String cleanPath = path.split("\\?")[0];
        return "rate-limit:" + cleanPath + ":" + clientId;
    }

    /**
     * 返回限流超出响应
     */
    @SuppressWarnings("null")
    private Mono<Void> rateLimitExceededResponse(ServerWebExchange exchange, String message) {
        exchange.getResponse().setStatusCode(HttpStatus.TOO_MANY_REQUESTS);
        exchange.getResponse().getHeaders().setContentType(MediaType.APPLICATION_JSON);

        String jsonResponse = String.format(
            "{\"code\": 429, \"message\": \"%s\", \"timestamp\": %d}",
            message,
            System.currentTimeMillis()
        );

        return exchange.getResponse()
            .writeWith(Mono.fromSupplier(() ->
                exchange.getResponse().bufferFactory().wrap(jsonResponse.getBytes())
            ));
    }

    /**
     * 设置过滤器优先级
     * HIGHEST_PRECEDENCE + 1: 在认证过滤器之后执行
     */
    @Override
    public int getOrder() {
        return Ordered.HIGHEST_PRECEDENCE + 2;
    }
}

package com.hcsy.spring.infra.filter;

import java.net.URI;

import org.springframework.core.Ordered;
import org.springframework.core.annotation.Order;
import org.springframework.http.HttpStatus;
import org.springframework.http.server.reactive.ServerHttpResponse;
import org.springframework.stereotype.Component;
import org.springframework.web.server.ServerWebExchange;
import org.springframework.web.server.WebFilter;
import org.springframework.web.server.WebFilterChain;

import reactor.core.publisher.Mono;

/**
 * 拦截 Swagger UI 的 home 页面请求（springdoc 的 SwaggerUiHome 会显示 Petstore 选择页），
 * 重定向到 /swagger-ui.html（springdoc 的 SwaggerWelcomeWebFlux 会返回带正确 API URL 的页面）
 */
@Component
@Order(Ordered.HIGHEST_PRECEDENCE)
public class SwaggerIndexRedirectWebFilter implements WebFilter {

    @SuppressWarnings("null")
    @Override
    public Mono<Void> filter(ServerWebExchange exchange, WebFilterChain chain) {
        String path = exchange.getRequest().getPath().value();
        // 拦截 springdoc SwaggerUiHome 处理的路径，重定向到正确的 Swagger UI 入口
        if ("/swagger-ui/index.html".equals(path) || "/swagger-ui/".equals(path)) {
            ServerHttpResponse response = exchange.getResponse();
            response.setStatusCode(HttpStatus.FOUND);
            response.getHeaders().setLocation(URI.create("/swagger-ui.html"));
            return response.setComplete();
        }
        return chain.filter(exchange);
    }
}

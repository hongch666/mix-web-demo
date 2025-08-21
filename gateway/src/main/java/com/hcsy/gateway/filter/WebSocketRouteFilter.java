package com.hcsy.gateway.filter;

import org.springframework.cloud.gateway.filter.GatewayFilter;
import org.springframework.cloud.gateway.filter.factory.AbstractGatewayFilterFactory;
import org.springframework.http.HttpHeaders;
import org.springframework.http.server.reactive.ServerHttpRequest;
import org.springframework.stereotype.Component;

@Component
public class WebSocketRouteFilter extends AbstractGatewayFilterFactory<Object> {

    @Override
    public GatewayFilter apply(Object config) {
        return (exchange, chain) -> {
            ServerHttpRequest request = exchange.getRequest();

            // 检查是否是WebSocket升级请求
            String upgrade = request.getHeaders().getFirst(HttpHeaders.UPGRADE);
            String connection = request.getHeaders().getFirst(HttpHeaders.CONNECTION);

            if ("websocket".equalsIgnoreCase(upgrade) &&
                    connection != null && connection.toLowerCase().contains("upgrade")) {

                // 修改请求头以确保正确的Host传递
                ServerHttpRequest mutatedRequest = request.mutate()
                        .header("X-Forwarded-Proto", "ws")
                        .header("X-Forwarded-Port", "8080")
                        .build();

                return chain.filter(exchange.mutate().request(mutatedRequest).build());
            }

            return chain.filter(exchange);
        };
    }
}

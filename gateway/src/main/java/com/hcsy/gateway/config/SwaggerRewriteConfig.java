package com.hcsy.gateway.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.cloud.gateway.filter.factory.rewrite.RewriteFunction;
import org.springframework.web.server.ServerWebExchange;

import reactor.core.publisher.Mono;

/**
 * 网关层 Swagger 文档重写配置
 * 将后端服务返回的 OpenAPI 规范中的服务器地址改写为网关地址
 */
@Configuration
public class SwaggerRewriteConfig {

    @Bean
    public RewriteFunction<String, String> swaggerRewriteFunction() {
        return new RewriteFunction<String, String>() {
            @Override
            public Mono<String> apply(ServerWebExchange exchange, String body) {
                // 将后端服务的内部地址替换为网关地址
                String gatewayHost = exchange.getRequest().getURI().getHost();
                int gatewayPort = exchange.getRequest().getURI().getPort();
                if (gatewayPort == -1) {
                    gatewayPort = 8080;
                }
                String gatewayUrl = "http://" + gatewayHost + ":" + gatewayPort;
                // 替换 Spring 服务返回的 servers 地址
                String modified = body.replaceAll("\"http://localhost:\\d+\"", "\"" + gatewayUrl + "\"");
                return Mono.just(modified);
            }
        };
    }
}

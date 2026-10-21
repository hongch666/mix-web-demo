package com.hcsy.spring.config;

import org.springframework.cloud.client.loadbalancer.LoadBalanced;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.reactive.function.client.WebClient;

/**
 * 装配支持服务名负载均衡的 WebClient 构建器，用于微服务间调用
 */
@Configuration
public class WebClientConfig {

    /**
     * 装配支持服务名负载均衡的 WebClient 构建器，用于微服务间调用
     */
    @Bean
    @LoadBalanced
    WebClient.Builder loadBalancedWebClientBuilder() {
        return WebClient.builder();
    }
}

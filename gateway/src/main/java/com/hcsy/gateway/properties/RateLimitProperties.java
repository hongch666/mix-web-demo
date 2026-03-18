package com.hcsy.gateway.properties;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

import java.util.HashMap;
import java.util.Map;

/**
 * 限流配置属性
 */
@Component
@ConfigurationProperties(prefix = "rate-limit")
@Data
public class RateLimitProperties {

    /**
     * 是否启用限流
     */
    private boolean enabled = true;

    /**
     * 限流路径配置
     * key: 路径模式 (如 /api_spring/**, /api_fastapi/*)
     * value: 限流配置
     */
    private Map<String, RateLimitPath> paths = new HashMap<>();

    @Data
    public static class RateLimitPath {
        /**
         * 令牌桶容量
         */
        private Integer capacity = 100;

        /**
         * 令牌填充速率 (每秒填充多少个令牌)
         */
        private Integer refillRate = 10;

        /**
         * 是否启用（可单独控制某些路径的启用/禁用）
         */
        private Boolean enabled = true;

        /**
         * 限流超出时的响应消息
         */
        private String message = "你的请求过于频繁，请稍后再试";
    }
}

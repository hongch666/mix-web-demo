package com.hcsy.gateway.properties;

import java.util.HashMap;
import java.util.Map;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

import lombok.Data;

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
     * 通用限流配置，作为所有路径配置的默认值
     */
    private RateLimitPath common = new RateLimitPath();

    /**
     * 限流路径配置
     * key: 路径模式 (如 /api_spring/**, /api_fastapi/*)
     * value: 限流配置
     */
    private Map<String, RateLimitPath> paths = new HashMap<>();

    public RateLimitPath mergeWithCommon(RateLimitPath pathConfig) {
        RateLimitPath merged = new RateLimitPath();
        merged.setCapacity(common.getCapacity());
        merged.setRefillRate(common.getRefillRate());
        merged.setEnabled(common.getEnabled());
        merged.setMessage(common.getMessage());

        if (pathConfig == null) {
            return merged;
        }

        if (pathConfig.getCapacity() != null) {
            merged.setCapacity(pathConfig.getCapacity());
        }
        if (pathConfig.getRefillRate() != null) {
            merged.setRefillRate(pathConfig.getRefillRate());
        }
        if (pathConfig.getEnabled() != null) {
            merged.setEnabled(pathConfig.getEnabled());
        }
        if (pathConfig.getMessage() != null) {
            merged.setMessage(pathConfig.getMessage());
        }

        return merged;
    }

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

package com.hcsy.spring.core.properties;

import java.time.Duration;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;

/**
 * 微服务客户端统一配置
 */
@Configuration
@ConfigurationProperties(prefix = "service-client")
public class ServiceClientProperties {

    /**
     * 微服务间调用统一的请求超时时间
     */
    private Duration timeout;

    public Duration getTimeout() {
        return timeout;
    }

    public void setTimeout(Duration timeout) {
        this.timeout = timeout;
    }
}

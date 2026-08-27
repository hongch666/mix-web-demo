package com.hcsy.spring.core.properties;

import java.time.Duration;

import org.springframework.boot.context.properties.ConfigurationProperties;

/**
 * 微服务客户端统一配置属性（构造器绑定，不可变）
 *
 * @param timeout 微服务间调用统一的请求超时时间
 */
@ConfigurationProperties(prefix = "service-client")
public record ServiceClientProperties(Duration timeout) {
}

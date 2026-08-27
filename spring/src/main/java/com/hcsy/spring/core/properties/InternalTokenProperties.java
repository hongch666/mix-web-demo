package com.hcsy.spring.core.properties;

import org.springframework.boot.context.properties.ConfigurationProperties;

/**
 * 内部服务令牌配置属性（构造器绑定，不可变）
 *
 * @param secret     签名密钥
 * @param expiration 令牌有效期（毫秒）
 */
@ConfigurationProperties(prefix = "internal-token")
public record InternalTokenProperties(String secret, long expiration) {
}

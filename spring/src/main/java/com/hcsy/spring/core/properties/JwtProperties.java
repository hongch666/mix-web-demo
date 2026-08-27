package com.hcsy.spring.core.properties;

import org.springframework.boot.context.properties.ConfigurationProperties;

/**
 * JWT 配置属性（构造器绑定，不可变）
 *
 * @param secret            签名密钥
 * @param accessExpiration  访问令牌有效期（毫秒）
 * @param refreshExpiration 刷新令牌有效期（毫秒）
 */
@ConfigurationProperties(prefix = "jwt")
public record JwtProperties(String secret, long accessExpiration, long refreshExpiration) {
}

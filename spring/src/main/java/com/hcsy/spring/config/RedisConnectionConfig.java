package com.hcsy.spring.config;

import java.time.Duration;

import org.springframework.boot.autoconfigure.data.redis.LettuceClientConfigurationBuilderCustomizer;
import org.springframework.boot.autoconfigure.data.redis.RedisProperties;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import io.lettuce.core.ClientOptions;
import io.lettuce.core.SocketOptions;
import io.lettuce.core.SocketOptions.KeepAliveOptions;
import io.lettuce.core.TimeoutOptions;
import lombok.RequiredArgsConstructor;

/**
 * Lettuce 连接配置
 * 开启 TCP keepalive，让半开连接被操作系统及时检测并触发自动重连，避免共享连接静默失效后所有命令超时到重启才恢复
 */
@Configuration
@RequiredArgsConstructor
public class RedisConnectionConfig {

    private final RedisProperties redisProperties;

    /**
     * 装配开启 TCP keepalive 与命令超时的 Lettuce 客户端定制器，避免共享连接静默失效
     */
    @Bean
    LettuceClientConfigurationBuilderCustomizer lettuceKeepAliveCustomizer() {
        Duration connectTimeout = redisProperties.getConnectTimeout() != null
            ? redisProperties.getConnectTimeout()
            : Duration.ofSeconds(10);
        SocketOptions socketOptions = SocketOptions.builder()
            .connectTimeout(connectTimeout)
            .keepAlive(KeepAliveOptions.builder()
                .idle(Duration.ofSeconds(60))
                .interval(Duration.ofSeconds(15))
                .count(3)
                .build())
            .build();
        return builder -> builder.clientOptions(ClientOptions.builder()
            .socketOptions(socketOptions)
            .timeoutOptions(TimeoutOptions.enabled())
            .build());
    }
}

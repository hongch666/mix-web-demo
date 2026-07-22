package com.hcsy.gateway.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.data.redis.connection.RedisStandaloneConfiguration;
import org.springframework.data.redis.connection.lettuce.LettuceConnectionFactory;
import org.springframework.data.redis.core.ReactiveStringRedisTemplate;

import com.hcsy.gateway.properties.RedisProperties;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

@Configuration
@RequiredArgsConstructor
@Slf4j
public class RedisConnectionConfig {

    private final RedisProperties redisProperties;

    @Bean
    @SuppressWarnings("null")
    LettuceConnectionFactory lettuceConnectionFactory() {
        RedisStandaloneConfiguration config = new RedisStandaloneConfiguration();

        if (redisProperties.getHost() != null) {
            config.setHostName(redisProperties.getHost());
        }
        if (redisProperties.getPort() != null) {
            config.setPort(redisProperties.getPort());
        }
        if (redisProperties.getDatabase() != null) {
            config.setDatabase(redisProperties.getDatabase());
        }

        if (redisProperties.getUsername() != null && !redisProperties.getUsername().isEmpty()) {
            config.setUsername(redisProperties.getUsername());
            log.info("[Redis] 用户名: {}", redisProperties.getUsername());
        }

        if (redisProperties.getPassword() != null && !redisProperties.getPassword().isEmpty()) {
            config.setPassword(redisProperties.getPassword());
            log.info("[Redis] 已设置密码");
        }

        log.info(
            "[Redis] 连接: {}:{}, DB: {}",
            redisProperties.getHost() != null ? redisProperties.getHost() : "unknown",
            redisProperties.getPort() != null ? redisProperties.getPort() : 0,
            redisProperties.getDatabase() != null ? redisProperties.getDatabase() : 0
        );

        return new LettuceConnectionFactory(config);
    }

    @SuppressWarnings("null")
    @Bean
    ReactiveStringRedisTemplate reactiveStringRedisTemplate(LettuceConnectionFactory lettuceConnectionFactory) {
        return new ReactiveStringRedisTemplate(lettuceConnectionFactory);
    }
}

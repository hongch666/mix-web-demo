package com.hcsy.spring.common.config;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.data.redis.connection.RedisConnectionFactory;
import org.springframework.data.redis.connection.RedisStandaloneConfiguration;
import org.springframework.data.redis.connection.lettuce.LettuceConnectionFactory;

import com.hcsy.spring.common.properties.RedisProperties;
import com.hcsy.spring.common.utils.Constants;
import com.hcsy.spring.common.utils.SimpleLogger;

@Configuration
@RequiredArgsConstructor
@Slf4j
public class RedisConnectionConfig {

    private final SimpleLogger logger;
    private final RedisProperties redisProperties;

    @Bean
    RedisConnectionFactory redisConnectionFactory() {
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

        // 只有当用户名不为空时才设置
        if (redisProperties.getUsername() != null && !redisProperties.getUsername().isEmpty()) {
            config.setUsername(redisProperties.getUsername());
            logger.info(Constants.REDIS_USER, redisProperties.getUsername());
        }

        // 只有当密码不为空时才设置
        if (redisProperties.getPassword() != null && !redisProperties.getPassword().isEmpty()) {
            config.setPassword(redisProperties.getPassword());
            logger.info(Constants.REDIS_PASSWORD);
        }

        log.info(
            Constants.REDIS_CONNECT,
            redisProperties.getHost() != null ? redisProperties.getHost() : "unknown",
            redisProperties.getPort() != null ? redisProperties.getPort() : 0,
            redisProperties.getDatabase() != null ? redisProperties.getDatabase() : 0
        );
        return new LettuceConnectionFactory(config);
    }
}

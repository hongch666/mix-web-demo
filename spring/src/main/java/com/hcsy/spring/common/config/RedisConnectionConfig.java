package com.hcsy.spring.common.config;

import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.data.redis.connection.RedisConnectionFactory;
import org.springframework.data.redis.connection.RedisStandaloneConfiguration;
import org.springframework.data.redis.connection.lettuce.LettuceConnectionFactory;

import com.hcsy.spring.common.utils.SimpleLogger;

@Configuration
@RequiredArgsConstructor
public class RedisConnectionConfig {

    private final SimpleLogger logger;

    @Value("${spring.data.redis.host:localhost}")
    private String host;

    @Value("${spring.data.redis.port:6379}")
    private int port;

    @Value("${spring.data.redis.database:0}")
    private int database;

    @Value("${spring.data.redis.username:}")
    private String username;

    @Value("${spring.data.redis.password:}")
    private String password;

    @Bean
    RedisConnectionFactory redisConnectionFactory() {
        RedisStandaloneConfiguration config = new RedisStandaloneConfiguration();
        config.setHostName(host);
        config.setPort(port);
        config.setDatabase(database);

        // 只有当用户名不为空时才设置
        if (username != null && !username.isEmpty()) {
            config.setUsername(username);
            logger.info("[Redis] 使用用户名 '%s' 连接", username);
        }

        // 只有当密码不为空时才设置
        if (password != null && !password.isEmpty()) {
            config.setPassword(password);
            logger.info("[Redis] 已设置密码认证");
        }

        logger.info("[Redis] 连接配置: %s:%d (DB: %d)", host, port, database);
        return new LettuceConnectionFactory(config);
    }
}

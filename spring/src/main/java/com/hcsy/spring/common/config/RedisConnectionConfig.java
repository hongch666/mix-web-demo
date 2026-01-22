package com.hcsy.spring.common.config;

import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.data.redis.connection.RedisConnectionFactory;
import org.springframework.data.redis.connection.RedisStandaloneConfiguration;
import org.springframework.data.redis.connection.lettuce.LettuceConnectionFactory;

import com.hcsy.spring.common.utils.Constants;
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
            logger.info(Constants.REDIS_USER, username);
        }

        // 只有当密码不为空时才设置
        if (password != null && !password.isEmpty()) {
            config.setPassword(password);
            logger.info(Constants.REDIS_PASSWORD);
        }

        logger.info(Constants.REDIS_CONNECT, host, port, database);
        return new LettuceConnectionFactory(config);
    }
}

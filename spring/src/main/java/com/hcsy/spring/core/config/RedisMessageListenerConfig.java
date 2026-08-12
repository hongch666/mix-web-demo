package com.hcsy.spring.core.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.data.redis.connection.ReactiveRedisConnectionFactory;
import org.springframework.data.redis.listener.ReactiveRedisMessageListenerContainer;

@Configuration
public class RedisMessageListenerConfig {
    @Bean
    ReactiveRedisMessageListenerContainer reactiveRedisMessageListenerContainer(
        ReactiveRedisConnectionFactory connectionFactory) {
        return new ReactiveRedisMessageListenerContainer(connectionFactory);
    }
}

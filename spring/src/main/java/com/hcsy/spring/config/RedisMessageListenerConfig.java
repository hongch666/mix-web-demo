package com.hcsy.spring.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.data.redis.connection.ReactiveRedisConnectionFactory;
import org.springframework.data.redis.listener.ReactiveRedisMessageListenerContainer;

/**
 * 装配用于订阅 Redis 失效通知的响应式消息监听容器
 */
@Configuration
public class RedisMessageListenerConfig {
    /**
     * 装配用于订阅 Redis 失效通知的响应式消息监听容器
     */
    @Bean
    ReactiveRedisMessageListenerContainer reactiveRedisMessageListenerContainer(
        ReactiveRedisConnectionFactory connectionFactory) {
        return new ReactiveRedisMessageListenerContainer(connectionFactory);
    }
}

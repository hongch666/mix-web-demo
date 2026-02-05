package com.hcsy.spring.common.config;

import org.springframework.amqp.core.Queue;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class RabbitMQConfig {

    @Bean
    Queue apiLogQueue() {
        return new Queue("api-log-queue", true); // durable
    }

    @Bean
    Queue logQueue() {
        return new Queue("log-queue", true); // durable
    }
}

package com.hcsy.spring.common.config;

import org.springframework.amqp.core.Queue;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class RabbitMQConfig {

    @Bean
    Queue testQueue() {
        return new Queue("test.queue", true); // durable
    }
}

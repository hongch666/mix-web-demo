package com.hcsy.spring.core.config;

import org.springframework.amqp.core.Queue;
import org.springframework.amqp.rabbit.connection.AbstractConnectionFactory;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import reactor.rabbitmq.RabbitFlux;
import reactor.rabbitmq.Sender;
import reactor.rabbitmq.SenderOptions;

@Configuration
public class RabbitMQConfig {

    @Bean
    Queue apiLogQueue() {
        return new Queue("api-log-queue", true); // 持久化队列
    }

    @Bean
    Queue logQueue() {
        return new Queue("article-log-queue", true); // 持久化队列
    }

    @Bean(destroyMethod = "close")
    Sender rabbitSender(AbstractConnectionFactory connectionFactory) {
        SenderOptions senderOptions = new SenderOptions()
                .connectionFactory(connectionFactory.getRabbitConnectionFactory());
        return RabbitFlux.createSender(senderOptions);
    }
}

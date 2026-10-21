package com.hcsy.spring.config;

import org.springframework.amqp.core.Queue;
import org.springframework.amqp.rabbit.connection.AbstractConnectionFactory;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import com.hcsy.spring.common.constants.RabbitQueues;

import reactor.rabbitmq.RabbitFlux;
import reactor.rabbitmq.Sender;
import reactor.rabbitmq.SenderOptions;

/**
 * 装配 RabbitMQ 持久化队列与基于 Reactor RabbitMQ 的响应式消息发送器
 */
@Configuration
public class RabbitMQConfig {

    /**
     * 声明持久化的 API 日志队列
     */
    @Bean
    Queue apiLogQueue() {
        return new Queue(RabbitQueues.API_LOG, true); // 持久化队列
    }

    /**
     * 声明持久化的文章日志队列
     */
    @Bean
    Queue logQueue() {
        return new Queue(RabbitQueues.ARTICLE_LOG, true); // 持久化队列
    }

    /**
     * 装配基于 Reactor RabbitMQ 并复用现有连接工厂的响应式消息发送器
     */
    @Bean(destroyMethod = "close")
    Sender rabbitSender(AbstractConnectionFactory connectionFactory) {
        SenderOptions senderOptions = new SenderOptions()
            .connectionFactory(connectionFactory.getRabbitConnectionFactory());
        return RabbitFlux.createSender(senderOptions);
    }
}

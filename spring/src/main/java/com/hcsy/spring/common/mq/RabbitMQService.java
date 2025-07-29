package com.hcsy.spring.common.mq;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.amqp.rabbit.annotation.RabbitListener;
import org.springframework.stereotype.Service;

import com.hcsy.spring.common.utils.SimpleLogger;

@Slf4j
@Service
@RequiredArgsConstructor
public class RabbitMQService {

    private final RabbitTemplate rabbitTemplate;
    private final SimpleLogger logger;

    // 发送消息
    public void sendMessage(String queueName, Object message) {
        rabbitTemplate.convertAndSend(queueName, message);
        logger.info("消息发送成功：{} -> {}", queueName, message);
    }

    // 接收消息
    @RabbitListener(queues = "test.queue")
    public void receiveMessage(String message) {
        logger.info("收到消息：{}", message);
    }
}

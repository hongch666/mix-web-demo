package com.hcsy.spring.common.mq;

import lombok.RequiredArgsConstructor;
import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.amqp.rabbit.annotation.RabbitListener;
import org.springframework.stereotype.Service;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.hcsy.spring.common.utils.SimpleLogger;

@Service
@RequiredArgsConstructor
public class RabbitMQService {

    private final RabbitTemplate rabbitTemplate;
    private final SimpleLogger logger;
    private final ObjectMapper objectMapper;

    /**
     * 发送消息到队列
     * ✨ 使用 JSON 序列化，确保与 NestJS 消费者兼容
     */
    public void sendMessage(String queueName, Object message) {
        try {
            // 将对象转换为 JSON 字符串
            String jsonMessage = objectMapper.writeValueAsString(message);

            // 发送 JSON 字符串到队列
            rabbitTemplate.convertAndSend(queueName, jsonMessage);

            logger.info(String.format("消息发送成功：%s -> %s", queueName, jsonMessage));
        } catch (Exception e) {
            logger.error(String.format("消息发送失败：%s", e.getMessage()), e);
            throw new RuntimeException("Failed to send message to queue: " + queueName, e);
        }
    }

    // 接收消息
    @RabbitListener(queues = "test.queue")
    public void receiveMessage(String message) {
        logger.info("收到消息：{}", message);
    }
}

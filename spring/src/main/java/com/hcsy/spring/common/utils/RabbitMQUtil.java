package com.hcsy.spring.common.utils;

import lombok.RequiredArgsConstructor;
import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.stereotype.Component;
import com.fasterxml.jackson.databind.ObjectMapper;

@Component
@RequiredArgsConstructor
public class RabbitMQUtil {

    private final RabbitTemplate rabbitTemplate;
    private final SimpleLogger logger;
    private final ObjectMapper objectMapper;

    /**
     * 发送消息到队列
     * 使用 JSON 序列化，确保与 NestJS 消费者兼容
     */
    public void sendMessage(String queueName, Object message) {
        try {
            // 将对象转换为 JSON 字符串
            String jsonMessage = objectMapper.writeValueAsString(message);

            // 发送 JSON 字符串到队列
            rabbitTemplate.convertAndSend(queueName, jsonMessage);

            logger.info("消息发送成功：%s -> %s", queueName, jsonMessage);
        } catch (Exception e) {
            logger.error("消息发送失败：%s", e.getMessage(), e);
            throw new RuntimeException("Failed to send message to queue: " + queueName, e);
        }
    }

    /**
     * 发送消息到指定的交换机和路由键
     */
    public void sendMessage(String exchange, String routingKey, Object message) {
        try {
            String jsonMessage = objectMapper.writeValueAsString(message);
            rabbitTemplate.convertAndSend(exchange, routingKey, jsonMessage);
            logger.info("消息发送成功：%s/%s -> %s", exchange, routingKey, jsonMessage);
        } catch (Exception e) {
            logger.error("消息发送失败：%s", e.getMessage(), e);
            throw new RuntimeException("Failed to send message to exchange: " + exchange, e);
        }
    }

    /**
     * 将消息转换为指定的对象类型
     */
    public <T> T convertMessage(String jsonMessage, Class<T> targetClass) {
        try {
            return objectMapper.readValue(jsonMessage, targetClass);
        } catch (Exception e) {
            logger.error("消息转换失败：%s", e.getMessage(), e);
            throw new RuntimeException("Failed to convert message", e);
        }
    }
}

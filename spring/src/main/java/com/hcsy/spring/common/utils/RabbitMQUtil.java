package com.hcsy.spring.common.utils;

import lombok.RequiredArgsConstructor;
import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.stereotype.Component;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.hcsy.spring.common.exceptions.BusinessException;

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

            logger.info(Constants.MSG_SEND_SUCCESS, queueName, jsonMessage);
        } catch (Exception e) {
            logger.error(Constants.MSG_SEND_FAIL + e.getMessage());
            throw new BusinessException(Constants.MSG_SEND_FAIL + queueName);
        }
    }

    /**
     * 发送消息到指定的交换机和路由键
     */
    public void sendMessage(String exchange, String routingKey, Object message) {
        try {
            String jsonMessage = objectMapper.writeValueAsString(message);
            rabbitTemplate.convertAndSend(exchange, routingKey, jsonMessage);
            logger.info(Constants.EXCHANGE_SEND_SUCCESS, exchange, routingKey, jsonMessage);
        } catch (Exception e) {
            logger.error(Constants.EXCHANGE_SEND_FAIL + e.getMessage());
            throw new BusinessException(Constants.EXCHANGE_SEND_FAIL + exchange);
        }
    }

    /**
     * 将消息转换为指定的对象类型
     */
    public <T> T convertMessage(String jsonMessage, Class<T> targetClass) {
        try {
            return objectMapper.readValue(jsonMessage, targetClass);
        } catch (Exception e) {
            logger.error(Constants.TRANSFORM_MSG_FAIL, e.getMessage(), e);
            throw new BusinessException(Constants.TRANSFORM_MSG_FAIL);
        }
    }
}

package com.hcsy.spring.common.utils;

import java.nio.charset.StandardCharsets;

import org.springframework.stereotype.Component;

import com.rabbitmq.client.AMQP;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.hcsy.spring.common.constants.HttpCode;
import com.hcsy.spring.common.constants.Messages;
import com.hcsy.spring.common.exceptions.BusinessException;

import lombok.RequiredArgsConstructor;
import reactor.core.publisher.Mono;
import reactor.rabbitmq.OutboundMessage;
import reactor.rabbitmq.Sender;

@Component
@RequiredArgsConstructor
public class RabbitMQUtil {

    private static final String DEFAULT_EXCHANGE = "";
    private static final AMQP.BasicProperties JSON_MESSAGE_PROPERTIES = new AMQP.BasicProperties.Builder()
            .contentType("application/json")
            .contentEncoding(StandardCharsets.UTF_8.name())
            .deliveryMode(2)
            .build();

    private final Sender sender;
    private final SimpleLogger logger;
    private final ObjectMapper objectMapper;

    /**
     * 发送消息到队列
     * 使用 JSON 序列化，确保与 NestJS 消费者兼容
     */
    public Mono<Void> sendMessage(String queueName, Object message) {
        return Mono.fromCallable(() -> objectMapper.writeValueAsString(message))
                .flatMap(jsonMessage -> sendWithConfirm(DEFAULT_EXCHANGE, queueName, jsonMessage)
                        .doOnSuccess(ignored -> logger.info(Messages.MSG_SEND_SUCCESS, queueName, jsonMessage)))
                .onErrorMap(error -> {
                    logger.error(Messages.MSG_SEND_FAIL + error.getMessage(), error);
                    return BusinessException.builder().httpStatus(HttpCode.INTERNAL_SERVER_ERROR)
                            .errorMessage(Messages.MSG_SEND_FAIL + queueName).cause(error).build();
                })
                .then();
    }

    /**
     * 发送消息到指定的交换机和路由键
     */
    public Mono<Void> sendMessage(String exchange, String routingKey, Object message) {
        return Mono.fromCallable(() -> objectMapper.writeValueAsString(message))
                .flatMap(jsonMessage -> sendWithConfirm(exchange, routingKey, jsonMessage)
                        .doOnSuccess(ignored -> logger.info(
                                Messages.EXCHANGE_SEND_SUCCESS, exchange, routingKey, jsonMessage)))
                .onErrorMap(error -> {
                    logger.error(Messages.EXCHANGE_SEND_FAIL + error.getMessage(), error);
                    return BusinessException.builder().httpStatus(HttpCode.INTERNAL_SERVER_ERROR)
                            .errorMessage(Messages.EXCHANGE_SEND_FAIL + exchange).cause(error).build();
                })
                .then();
    }

    private Mono<Void> sendWithConfirm(String exchange, String routingKey, String jsonMessage) {
        OutboundMessage outboundMessage = new OutboundMessage(
                exchange,
                routingKey,
                JSON_MESSAGE_PROPERTIES,
                jsonMessage.getBytes(StandardCharsets.UTF_8));
        return sender.sendWithPublishConfirms(Mono.just(outboundMessage))
                .single()
                .flatMap(result -> result.isAck()
                        ? Mono.empty()
                        : Mono.error(new IllegalStateException(Messages.RABBITMQ_MESSAGE_UNCONFIRMED)));
    }

    /**
     * 将消息转换为指定的对象类型
     */
    public <T> T convertMessage(String jsonMessage, Class<T> targetClass) {
        try {
            return objectMapper.readValue(jsonMessage, targetClass);
        } catch (Exception e) {
            logger.error(Messages.TRANSFORM_MSG_FAIL, e.getMessage(), e);
            throw BusinessException.builder().httpStatus(HttpCode.INTERNAL_SERVER_ERROR).errorMessage(Messages.TRANSFORM_MSG_FAIL).build();
        }
    }
}

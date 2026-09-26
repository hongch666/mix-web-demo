package com.hcsy.spring.common.utils;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import com.hcsy.spring.common.exceptions.BusinessException;

import com.fasterxml.jackson.databind.ObjectMapper;
import reactor.rabbitmq.Sender;
import reactor.test.StepVerifier;

class RabbitMQUtilTest {
    // 验证该场景的预期行为
    @Test
    @DisplayName("消息转换失败时返回业务异常")
    void convertsInvalidMessageToBusinessError() {
        RabbitMQUtil util = new RabbitMQUtil(mock(Sender.class), mock(SimpleLogger.class), new ObjectMapper());
        try {
            util.convertMessage("{", Object.class);
        } catch (BusinessException ex) {
            assertEquals(500, ex.getHttpStatus());
        }
    }

    // 验证该场景的预期行为

    @Test
    @DisplayName("发送消息序列化失败时返回错误")
    void sendFailureIsReactiveError() {
        ObjectMapper mapper = mock(ObjectMapper.class);
        try {
            when(mapper.writeValueAsString("x")).thenThrow(new RuntimeException("bad"));
        } catch (Exception ignored) {
        }
        RabbitMQUtil util = new RabbitMQUtil(mock(Sender.class), mock(SimpleLogger.class), mapper);
        StepVerifier.create(util.sendMessage("q", "x")).expectError(BusinessException.class).verify();
    }
}

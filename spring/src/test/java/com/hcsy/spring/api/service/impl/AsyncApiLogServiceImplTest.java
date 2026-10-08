package com.hcsy.spring.api.service.impl;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import java.util.Map;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import com.hcsy.spring.common.utils.RabbitMQUtil;
import com.hcsy.spring.common.utils.SimpleLogger;

import reactor.core.publisher.Mono;
import reactor.test.StepVerifier;

@ExtendWith(MockitoExtension.class)
class AsyncApiLogServiceImplTest {

    private static final String QUEUE_NAME = "api-log-queue";

    @Mock
    private RabbitMQUtil rabbitMQUtil;
    @Mock
    private SimpleLogger logger;

    private AsyncApiLogServiceImpl asyncApiLogService;

    @BeforeEach
    void setUp() {
        asyncApiLogService = new AsyncApiLogServiceImpl(rabbitMQUtil, logger);
    }

    @Test
    @DisplayName("发送接口日志时按固定队列投递原始报文")
    void sendAsyncPublishesToApiLogQueue() {
        Map<String, Object> message = Map.of("path", "/articles", "status", 200);
        when(rabbitMQUtil.sendMessage(eq(QUEUE_NAME), any())).thenReturn(Mono.empty());

        StepVerifier.create(asyncApiLogService.sendAsync(message)).verifyComplete();

        ArgumentCaptor<Object> payloadCaptor = ArgumentCaptor.forClass(Object.class);
        verify(rabbitMQUtil).sendMessage(eq(QUEUE_NAME), payloadCaptor.capture());
        assertThat(payloadCaptor.getValue()).isEqualTo(message);
    }

    @Test
    @DisplayName("投递失败时降级为完成而不是向外抛错")
    void sendAsyncSwallowsMQFailure() {
        Map<String, Object> message = Map.of("path", "/articles");
        when(rabbitMQUtil.sendMessage(eq(QUEUE_NAME), any()))
            .thenReturn(Mono.error(new IllegalStateException("mq down")));

        StepVerifier.create(asyncApiLogService.sendAsync(message)).verifyComplete();

        verify(rabbitMQUtil).sendMessage(eq(QUEUE_NAME), any());
    }

    @Test
    @DisplayName("投递成功后不写入错误日志")
    void sendAsyncDoesNotLogErrorOnSuccess() {
        when(rabbitMQUtil.sendMessage(anyString(), any())).thenReturn(Mono.empty());

        StepVerifier.create(asyncApiLogService.sendAsync(Map.of("path", "/articles"))).verifyComplete();

        verify(logger, never()).error(anyString());
    }
}

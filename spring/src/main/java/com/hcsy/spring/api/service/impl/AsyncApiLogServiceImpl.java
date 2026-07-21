package com.hcsy.spring.api.service.impl;

import java.util.Map;

import org.springframework.stereotype.Service;

import com.hcsy.spring.api.service.AsyncApiLogService;
import com.hcsy.spring.common.utils.RabbitMQUtil;
import com.hcsy.spring.common.utils.SimpleLogger;

import lombok.RequiredArgsConstructor;
import reactor.core.publisher.Mono;
import reactor.core.scheduler.Schedulers;

/**
 * API 日志异步发送服务实现
 * 将 API 日志异步发送到 RabbitMQ，不阻塞业务接口响应
 */
@Service
@RequiredArgsConstructor
public class AsyncApiLogServiceImpl implements AsyncApiLogService {

    private final RabbitMQUtil rabbitMQUtil;
    private final SimpleLogger logger;

    @Override
    public void sendAsync(Map<String, Object> apiLogMessage) {
        Mono.fromRunnable(() -> {
            try {
                rabbitMQUtil.sendMessage("api-log-queue", apiLogMessage);
                logger.info("API 日志异步发送成功");
            } catch (Exception e) {
                logger.error("API 日志异步发送失败: {}", e.getMessage(), e);
                // 不抛出异常，避免影响异步线程池
            }
        }).subscribeOn(Schedulers.boundedElastic()).subscribe();
    }
}

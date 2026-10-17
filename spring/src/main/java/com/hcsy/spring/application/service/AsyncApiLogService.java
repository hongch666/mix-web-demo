package com.hcsy.spring.application.service;

import com.hcsy.spring.entity.event.ApiLogEvent;

import reactor.core.publisher.Mono;

/**
 * API 日志异步发送服务接口
 * 用于在后台异步发送 API 日志到 RabbitMQ，不阻塞业务接口响应
 */
public interface AsyncApiLogService {

    /**
     * 异步发送 API 日志到消息队列
     * 此方法会在后台线程池中执行，不阻塞主流程
     *
     * @param apiLogEvent
     *                        接口日志事件
     */
    Mono<Void> sendAsync(ApiLogEvent apiLogEvent);
}

package com.hcsy.spring.api.service;

import java.util.Map;

/**
 * API 日志异步发送服务接口
 * 用于在后台异步发送 API 日志到 RabbitMQ，不阻塞业务接口响应
 */
public interface AsyncApiLogService {

    /**
     * 异步发送 API 日志到消息队列
     * 此方法会在后台线程池中执行，不阻塞主流程
     *
     * @param apiLogMessage API 日志消息 Map
     */
    void sendAsync(Map<String, Object> apiLogMessage);
}

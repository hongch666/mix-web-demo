package com.hcsy.spring.application.service;

import reactor.core.publisher.Mono;

/**
 * 定时任务触发业务接口，定义手动触发定时任务并交由后台异步执行的响应式操作
 */
public interface TaskService {
    /**
     * 手动触发一次过期Token清理任务，任务流程在后台异步执行并立即返回Mono空信号
     */
    Mono<Void> triggerTokenCleanup();
}

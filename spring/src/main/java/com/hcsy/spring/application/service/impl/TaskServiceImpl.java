package com.hcsy.spring.application.service.impl;

import org.springframework.stereotype.Service;

import com.hcsy.spring.application.service.TaskService;
import com.hcsy.spring.application.task.TokenCleanupTask;
import com.hcsy.spring.common.constants.Messages;
import com.hcsy.spring.common.utils.SimpleLogger;

import lombok.RequiredArgsConstructor;
import reactor.core.publisher.Mono;

/**
 * 定时任务触发服务实现，调用任务组件的清理流程并负责后台异步执行与错误兜底日志
 */
@Service
@RequiredArgsConstructor
public class TaskServiceImpl implements TaskService {

    private final TokenCleanupTask tokenCleanupTask;
    private final SimpleLogger logger;

    /**
     * 手动触发一次过期Token清理任务，订阅任务流程使其在后台异步执行，错误仅记录日志不向上传播
     */
    @Override
    public Mono<Void> triggerTokenCleanup() {
        return Mono.fromRunnable(() -> tokenCleanupTask.cleanupExpiredTokens()
            .doOnError(error -> logger.error(Messages.TASK_EXCEPTION + error.getMessage(), error))
            .onErrorResume(error -> Mono.empty())
            .subscribe());
    }
}

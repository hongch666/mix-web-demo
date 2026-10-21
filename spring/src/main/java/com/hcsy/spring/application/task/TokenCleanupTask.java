package com.hcsy.spring.application.task;

import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

import com.hcsy.spring.application.service.TokenService;
import com.hcsy.spring.common.constants.Defaults;
import com.hcsy.spring.common.constants.Messages;
import com.hcsy.spring.common.constants.RedisKeys;
import com.hcsy.spring.common.utils.RedisDistributedLock;
import com.hcsy.spring.common.utils.SimpleLogger;
import com.hcsy.spring.observability.MetricsRecorder;

import lombok.RequiredArgsConstructor;
import reactor.core.publisher.Mono;

/**
 * 过期Token定时清理任务，每分钟通过 Redis 分布式锁防止多实例重复执行，并记录任务成功失败状态与耗时指标
 */
@Component
@RequiredArgsConstructor
public class TokenCleanupTask {

    private final TokenService tokenService;
    private final SimpleLogger logger;
    private final RedisDistributedLock distributedLock;
    private final MetricsRecorder metricsRecorder;

    /**
     * 手动触发一次过期Token清理任务，异步执行清理流程并记录过程中的错误日志
     */
    public void triggerCleanup() {
        cleanupExpiredTokens()
            .doOnError(error -> logger.error(Messages.TASK_EXCEPTION + error.getMessage(), error))
            .subscribe();
    }

    /**
     * 每分钟定时清理过期登录Token，通过Redis分布式锁防止多实例重复执行，并记录任务成功失败状态与耗时指标
     */
    @Scheduled(cron = "0 * * * * *")
    public Mono<Void> cleanupExpiredTokens() {
        long startedAt = System.nanoTime();
        String lockKey = RedisKeys.lockTaskTokenCleanup();
        return distributedLock.tryLock(lockKey, Defaults.LOCK_TASK_TOKEN_CLEANUP_EXPIRE)
            .doOnNext(ignored -> logger.info(String.format(Messages.LOCK_ACQUIRE_SUCCESS, lockKey)))
            .flatMap(lockValue -> tokenService.cleanupExpiredTokens()
                .doOnSubscribe(ignored -> logger.info(Messages.TASK_START))
                .doOnSuccess(ignored -> logger.info(Messages.TASK_END))
                .doOnSuccess(ignored -> metricsRecorder.recordTask(
                    "token-cleanup", "success", System.nanoTime() - startedAt))
                .doOnError(error -> {
                    metricsRecorder.recordTask(
                        "token-cleanup", "failure", System.nanoTime() - startedAt);
                    logger.error(Messages.TASK_EXCEPTION + error.getMessage(), error);
                })
                .onErrorResume(error -> Mono.empty())
                .then(distributedLock.unlock(lockKey, lockValue))
                .doOnNext(released -> {
                    if (released) {
                        logger.info(String.format(Messages.LOCK_RELEASE_SUCCESS, lockKey));
                    } else {
                        logger.warning(String.format(Messages.LOCK_RELEASE_FAIL, lockKey));
                    }
                })
                .then())
            .switchIfEmpty(Mono.fromRunnable(
                () -> logger.info(String.format(Messages.LOCK_ACQUIRE_FAIL, lockKey))));
    }
}

package com.hcsy.spring.infra.task;

import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

import com.hcsy.spring.api.service.TokenService;
import com.hcsy.spring.common.constants.Defaults;
import com.hcsy.spring.common.constants.Messages;
import com.hcsy.spring.common.constants.RedisKeys;
import com.hcsy.spring.common.utils.RedisDistributedLock;
import com.hcsy.spring.common.utils.SimpleLogger;
import com.hcsy.spring.core.metrics.MetricsRecorder;

import lombok.RequiredArgsConstructor;
import reactor.core.publisher.Mono;

@Component
@RequiredArgsConstructor
public class TokenCleanupTask {

    private final TokenService tokenService;
    private final SimpleLogger logger;
    private final RedisDistributedLock distributedLock;
    private final MetricsRecorder metricsRecorder;

    @Scheduled(cron = "0 0 * * * *")
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

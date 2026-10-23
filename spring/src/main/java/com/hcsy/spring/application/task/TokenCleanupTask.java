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

import io.opentelemetry.api.GlobalOpenTelemetry;
import io.opentelemetry.api.trace.Span;
import io.opentelemetry.api.trace.Tracer;
import io.opentelemetry.context.Scope;
import lombok.RequiredArgsConstructor;
import reactor.core.publisher.Mono;

/**
 * 过期Token定时清理任务，每分钟通过 Redis 分布式锁防止多实例重复执行，并记录任务成功失败状态与耗时指标
 * 手动触发路径由 TaskService 订阅本任务的清理流程完成后台执行
 */
@Component
@RequiredArgsConstructor
public class TokenCleanupTask {

    private final TokenService tokenService;
    private final SimpleLogger logger;
    private final RedisDistributedLock distributedLock;
    private final MetricsRecorder metricsRecorder;

    /**
     * 每分钟定时清理过期登录Token，通过Redis分布式锁防止多实例重复执行，并记录任务成功失败状态与耗时指标
     */
    @Scheduled(cron = "0 * * * * *")
    public Mono<Void> cleanupExpiredTokens() {
        long startedAt = System.nanoTime();
        String lockKey = RedisKeys.lockTaskTokenCleanup();
        // 定时任务没有请求入口，手动开启一段根 span，让本次执行的日志关联到同一个 trace_id
        Tracer tracer = GlobalOpenTelemetry.get().getTracer("spring");
        Span span = tracer.spanBuilder("job:token-cleanup").startSpan();

        return distributedLock.tryLock(lockKey, Defaults.LOCK_TASK_TOKEN_CLEANUP_EXPIRE)
            .switchIfEmpty(Mono.fromRunnable(
                () -> logInfo(span, String.format(Messages.LOCK_ACQUIRE_FAIL, lockKey))))
            .doOnNext(ignored -> logInfo(span, String.format(Messages.LOCK_ACQUIRE_SUCCESS, lockKey)))
            .flatMap(lockValue -> tokenService.cleanupExpiredTokens()
                .doOnSubscribe(ignored -> logInfo(span, Messages.TASK_START))
                .doOnSuccess(ignored -> logInfo(span, Messages.TASK_END))
                .doOnSuccess(ignored -> metricsRecorder.recordTask(
                    "token-cleanup", "success", System.nanoTime() - startedAt))
                .doOnError(error -> {
                    metricsRecorder.recordTask(
                        "token-cleanup", "failure", System.nanoTime() - startedAt);
                    span.recordException(error);
                    logError(span, Messages.TASK_EXCEPTION + error.getMessage(), error);
                })
                .onErrorResume(error -> Mono.empty())
                .then(distributedLock.unlock(lockKey, lockValue))
                .doOnNext(released -> {
                    if (released) {
                        logInfo(span, String.format(Messages.LOCK_RELEASE_SUCCESS, lockKey));
                    } else {
                        logWarning(span, String.format(Messages.LOCK_RELEASE_FAIL, lockKey));
                    }
                })
                .then())
            .doFinally(signalType -> span.end());
    }

    // 响应式链路会切换线程，span 无法通过 makeCurrent 自动贯穿整个链条，
    // 因此在每个日志点把任务 span 显式置为当前，让 SimpleLogger 取到本次执行的 trace_id
    private void logInfo(Span span, String message) {
        try (Scope ignored = span.makeCurrent()) {
            logger.info(message);
        }
    }

    private void logWarning(Span span, String message) {
        try (Scope ignored = span.makeCurrent()) {
            logger.warning(message);
        }
    }

    private void logError(Span span, String message, Throwable error) {
        try (Scope ignored = span.makeCurrent()) {
            logger.error(message, error);
        }
    }
}

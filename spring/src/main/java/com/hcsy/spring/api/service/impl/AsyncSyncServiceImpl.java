package com.hcsy.spring.api.service.impl;

import java.util.concurrent.Executor;

import org.springframework.stereotype.Service;

import jakarta.annotation.Resource;

import com.hcsy.spring.api.service.AsyncSyncService;
import com.hcsy.spring.common.constants.Messages;
import com.hcsy.spring.common.constants.Defaults;
import com.hcsy.spring.common.utils.SimpleLogger;
import com.hcsy.spring.infra.client.FastAPIClient;
import com.hcsy.spring.infra.client.GoZeroClient;

import lombok.RequiredArgsConstructor;
import reactor.core.publisher.Mono;
import reactor.core.scheduler.Schedulers;

/**
 * 增强的异步同步服务实现
 * 支持并行执行、超时控制、重试机制
 */
@Service
@RequiredArgsConstructor
public class AsyncSyncServiceImpl implements AsyncSyncService {

    private final GoZeroClient goZeroClient;
    private final FastAPIClient fastAPIClient;
    private final SimpleLogger logger;

    @Resource(name = "syncTaskExecutor")
    private Executor syncTaskExecutor;

    private static final int MAX_RETRY_TIMES = 3;
    private static final long RETRY_DELAY_MS = 1000;

    /**
     * 并行异步同步 ES、Vector 和缓存清理
     * 使用 Mono 实现并行执行
     */
    @Override
    public void syncAllAsync(Long userId, String username) {
        String user = (username != null ? username : Defaults.DEFAULT_USER) +
                     ":" +
                     (userId != null ? userId : Defaults.DEFAULT_USER_ID);

        Mono.fromRunnable(() -> {
            long startTime = System.currentTimeMillis();
            try {
                logger.info(user + Messages.SYNC);

                // 并行执行三个同步任务
                Mono<Void> esMono = Mono.fromRunnable(() -> { syncESWithRetry(MAX_RETRY_TIMES); })
                    .subscribeOn(Schedulers.boundedElastic()).then();
                Mono<Void> vectorMono = Mono.fromRunnable(() -> { syncVectorWithRetry(MAX_RETRY_TIMES); })
                    .subscribeOn(Schedulers.boundedElastic()).then();
                Mono<Void> cacheMono = Mono.fromRunnable(() -> { clearCacheWithRetry(MAX_RETRY_TIMES); })
                    .subscribeOn(Schedulers.boundedElastic()).then();

                Mono.when(esMono, vectorMono, cacheMono)
                    .doOnSuccess(v -> {
                        long duration = System.currentTimeMillis() - startTime;
                        logger.info(Messages.SYNC_PARALLEL_SUCCESS, user, duration);
                        logger.info(Messages.SYNC_ALL_SUCCESS);
                    })
                    .doOnError(e -> {
                        long duration = System.currentTimeMillis() - startTime;
                        logger.error(Messages.SYNC_PARALLEL_FAIL, user, duration, e.getMessage(), e);
                    })
                    .subscribe();

            } catch (Exception e) {
                logger.error(Messages.SYNC_ALL_FAIL + e.getMessage(), e);
            }
        }).subscribeOn(Schedulers.boundedElastic()).subscribe();
    }

    /**
     * 带重试机制的 ES 同步
     */
    private void syncESWithRetry(int maxRetries) {
        int retryCount = 0;
        while (retryCount <= maxRetries) {
            try {
                long startTime = System.currentTimeMillis();
                goZeroClient.syncES();
                long duration = System.currentTimeMillis() - startTime;
                logger.info(Messages.SYNC_ES_DURATION, duration);
                logger.info(Messages.SYNC_ES_SUCCESS);
                return;
            } catch (Exception e) {
                retryCount++;
                if (retryCount <= maxRetries) {
                    logger.warning(Messages.SYNC_ES_RETRY, retryCount, e.getMessage());
                    try {
                        Thread.sleep(RETRY_DELAY_MS);
                    } catch (InterruptedException ie) {
                        Thread.currentThread().interrupt();
                        throw new RuntimeException(Messages.SYNC_ES_RETRY_INTERRUPTED, ie);
                    }
                } else {
                    logger.error(Messages.SYNC_ES_MAX_RETRY, e.getMessage(), e);
                    throw new RuntimeException(Messages.SYNC_ES_FAILED, e);
                }
            }
        }
    }

    /**
     * 带重试机制的 Vector 同步
     */
    private void syncVectorWithRetry(int maxRetries) {
        int retryCount = 0;
        while (retryCount <= maxRetries) {
            try {
                long startTime = System.currentTimeMillis();
                fastAPIClient.syncVector();
                long duration = System.currentTimeMillis() - startTime;
                logger.info(Messages.SYNC_VECTOR_DURATION, duration);
                logger.info(Messages.SYNC_VECTOR_SUCCESS);
                return;
            } catch (Exception e) {
                retryCount++;
                if (retryCount <= maxRetries) {
                    logger.warning(Messages.SYNC_VECTOR_RETRY, retryCount, e.getMessage());
                    try {
                        Thread.sleep(RETRY_DELAY_MS);
                    } catch (InterruptedException ie) {
                        Thread.currentThread().interrupt();
                        throw new RuntimeException(Messages.SYNC_VECTOR_RETRY_INTERRUPTED, ie);
                    }
                } else {
                    logger.error(Messages.SYNC_VECTOR_MAX_RETRY, e.getMessage(), e);
                    throw new RuntimeException(Messages.SYNC_VECTOR_FAILED, e);
                }
            }
        }
    }

    /**
     * 带重试机制的缓存清理
     */
    private void clearCacheWithRetry(int maxRetries) {
        int retryCount = 0;
        while (retryCount <= maxRetries) {
            try {
                long startTime = System.currentTimeMillis();
                fastAPIClient.clearAnalyzeCaches();
                long duration = System.currentTimeMillis() - startTime;
                logger.info(Messages.CACHE_CLEAR_DURATION, duration);
                logger.info(Messages.CLEAR_CACHE_SUCCESS);
                return;
            } catch (Exception e) {
                retryCount++;
                if (retryCount <= maxRetries) {
                    logger.warning(Messages.CACHE_CLEAR_RETRY, retryCount, e.getMessage());
                    try {
                        Thread.sleep(RETRY_DELAY_MS);
                    } catch (InterruptedException ie) {
                        Thread.currentThread().interrupt();
                        throw new RuntimeException(Messages.CACHE_CLEAR_RETRY_INTERRUPTED, ie);
                    }
                } else {
                    logger.error(Messages.CACHE_CLEAR_MAX_RETRY, e.getMessage(), e);
                    throw new RuntimeException(Messages.CACHE_CLEAR_FAILED, e);
                }
            }
        }
    }
}

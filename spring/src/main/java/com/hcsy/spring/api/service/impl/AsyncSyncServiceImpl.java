package com.hcsy.spring.api.service.impl;

import java.util.concurrent.CompletableFuture;
import java.util.concurrent.TimeUnit;

import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;

import com.hcsy.spring.api.service.AsyncSyncService;
import com.hcsy.spring.common.utils.Constants;
import com.hcsy.spring.common.utils.SimpleLogger;
import com.hcsy.spring.common.utils.UserContext;
import com.hcsy.spring.infra.client.FastAPIClient;
import com.hcsy.spring.infra.client.GoZeroClient;

import lombok.RequiredArgsConstructor;

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

    private static final int SYNC_TIMEOUT_SECONDS = 30;
    private static final int MAX_RETRY_TIMES = 3;
    private static final long RETRY_DELAY_MS = 1000;

    /**
     * 并行异步同步 ES、Vector 和缓存清理
     * 使用 CompletableFuture 实现并行执行和超时控制
     *
     * @param userId   触发同步的用户ID
     * @param username 触发同步的用户名
     */
    @Override
    @Async("asyncExecutor")
    public void syncAllAsync(Long userId, String username) {
        long startTime = System.currentTimeMillis();
        String user = (username != null ? username : Constants.DEFAULT_USER) +
                     ":" +
                     (userId != null ? userId : Constants.DEFAULT_USER_ID);

        try {
            logger.info(user + Constants.SYNC);

            CompletableFuture<Void> esFuture = CompletableFuture.runAsync(
                () -> syncESWithRetry(MAX_RETRY_TIMES),
                CompletableFuture.delayedExecutor(0, TimeUnit.MILLISECONDS)
            );

            CompletableFuture<Void> vectorFuture = CompletableFuture.runAsync(
                () -> syncVectorWithRetry(MAX_RETRY_TIMES),
                CompletableFuture.delayedExecutor(0, TimeUnit.MILLISECONDS)
            );

            CompletableFuture<Void> cacheFuture = CompletableFuture.runAsync(
                () -> clearCacheWithRetry(MAX_RETRY_TIMES),
                CompletableFuture.delayedExecutor(0, TimeUnit.MILLISECONDS)
            );

            CompletableFuture.allOf(esFuture, vectorFuture, cacheFuture)
                .get(SYNC_TIMEOUT_SECONDS, TimeUnit.SECONDS);

            long duration = System.currentTimeMillis() - startTime;
            logger.info(Constants.SYNC_PARALLEL_SUCCESS, user, duration);
            logger.info(Constants.SYNC_ALL_SUCCESS);

        } catch (Exception e) {
            long duration = System.currentTimeMillis() - startTime;
            logger.error(Constants.SYNC_PARALLEL_FAIL, user, duration, e.getMessage(), e);
        } finally {
            UserContext.clear();
            logger.debug(Constants.CLEAN_CONTEXT);
        }
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
                logger.info(Constants.SYNC_ES_DURATION, duration);
                logger.info(Constants.SYNC_ES_SUCCESS);
                return;
            } catch (Exception e) {
                retryCount++;
                if (retryCount <= maxRetries) {
                    logger.warning(Constants.SYNC_ES_RETRY, retryCount, e.getMessage());
                    try {
                        Thread.sleep(RETRY_DELAY_MS);
                    } catch (InterruptedException ie) {
                        Thread.currentThread().interrupt();
                        throw new RuntimeException(Constants.SYNC_ES_RETRY_INTERRUPTED, ie);
                    }
                } else {
                    logger.error(Constants.SYNC_ES_MAX_RETRY, e.getMessage(), e);
                    throw new RuntimeException(Constants.SYNC_ES_FAILED, e);
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
                logger.info(Constants.SYNC_VECTOR_DURATION, duration);
                logger.info(Constants.SYNC_VECTOR_SUCCESS);
                return;
            } catch (Exception e) {
                retryCount++;
                if (retryCount <= maxRetries) {
                    logger.warning(Constants.SYNC_VECTOR_RETRY, retryCount, e.getMessage());
                    try {
                        Thread.sleep(RETRY_DELAY_MS);
                    } catch (InterruptedException ie) {
                        Thread.currentThread().interrupt();
                        throw new RuntimeException(Constants.SYNC_VECTOR_RETRY_INTERRUPTED, ie);
                    }
                } else {
                    logger.error(Constants.SYNC_VECTOR_MAX_RETRY, e.getMessage(), e);
                    throw new RuntimeException(Constants.SYNC_VECTOR_FAILED, e);
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
                logger.info(Constants.CACHE_CLEAR_DURATION, duration);
                logger.info(Constants.CLEAR_CACHE_SUCCESS);
                return;
            } catch (Exception e) {
                retryCount++;
                if (retryCount <= maxRetries) {
                    logger.warning(Constants.CACHE_CLEAR_RETRY, retryCount, e.getMessage());
                    try {
                        Thread.sleep(RETRY_DELAY_MS);
                    } catch (InterruptedException ie) {
                        Thread.currentThread().interrupt();
                        throw new RuntimeException(Constants.CACHE_CLEAR_RETRY_INTERRUPTED, ie);
                    }
                } else {
                    logger.error(Constants.CACHE_CLEAR_MAX_RETRY, e.getMessage(), e);
                    throw new RuntimeException(Constants.CACHE_CLEAR_FAILED, e);
                }
            }
        }
    }

}

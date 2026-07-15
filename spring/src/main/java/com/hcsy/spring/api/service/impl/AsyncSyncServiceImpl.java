package com.hcsy.spring.api.service.impl;

import java.util.concurrent.CompletableFuture;
import java.util.concurrent.Executor;
import java.util.concurrent.TimeUnit;

import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;

import jakarta.annotation.Resource;

import com.hcsy.spring.api.service.AsyncSyncService;
import com.hcsy.spring.common.exceptions.BusinessException;
import com.hcsy.spring.common.constants.Messages;
import com.hcsy.spring.common.constants.Defaults;
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

    @Resource(name = "syncTaskExecutor")
    private Executor syncTaskExecutor;

    private static final int SYNC_TIMEOUT_SECONDS = 300;
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
    @Async("syncTaskExecutor")
    public void syncAllAsync(Long userId, String username) {
        long startTime = System.currentTimeMillis();
        String user = (username != null ? username : Defaults.DEFAULT_USER) +
                     ":" +
                     (userId != null ? userId : Defaults.DEFAULT_USER_ID);

        try {
            logger.info(user + Messages.SYNC);

            // 使用 CompletableFuture + syncTaskExecutor 并行执行ES同步
            CompletableFuture<Void> esFuture = CompletableFuture.runAsync(
                () -> syncESWithRetry(MAX_RETRY_TIMES),
                syncTaskExecutor
            );

            // 使用 CompletableFuture + syncTaskExecutor 并行执行Vector同步
            CompletableFuture<Void> vectorFuture = CompletableFuture.runAsync(
                () -> syncVectorWithRetry(MAX_RETRY_TIMES),
                syncTaskExecutor
            );

            // 使用 CompletableFuture + syncTaskExecutor 并行执行缓存清理
            CompletableFuture<Void> cacheFuture = CompletableFuture.runAsync(
                () -> clearCacheWithRetry(MAX_RETRY_TIMES),
                syncTaskExecutor
            );

            CompletableFuture.allOf(esFuture, vectorFuture, cacheFuture)
                .get(SYNC_TIMEOUT_SECONDS, TimeUnit.SECONDS);

            long duration = System.currentTimeMillis() - startTime;
            logger.info(Messages.SYNC_PARALLEL_SUCCESS, user, duration);
            logger.info(Messages.SYNC_ALL_SUCCESS);

        } catch (Exception e) {
            long duration = System.currentTimeMillis() - startTime;
            logger.error(Messages.SYNC_PARALLEL_FAIL, user, duration, e.getMessage(), e);
        } finally {
            UserContext.clear();
            logger.debug(Messages.CLEAN_CONTEXT);
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
                        throw BusinessException.builder().errorCode(Messages.SYNC_ES_RETRY_INTERRUPTED).cause(ie).build();
                    }
                } else {
                    logger.error(Messages.SYNC_ES_MAX_RETRY, e.getMessage(), e);
                    throw BusinessException.builder().errorCode(Messages.SYNC_ES_FAILED).cause(e).build();
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

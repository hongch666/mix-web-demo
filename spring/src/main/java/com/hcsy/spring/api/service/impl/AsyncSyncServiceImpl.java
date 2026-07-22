package com.hcsy.spring.api.service.impl;

import java.time.Duration;
import java.util.function.Supplier;

import org.springframework.stereotype.Service;

import com.hcsy.spring.api.service.AsyncSyncService;
import com.hcsy.spring.common.constants.Defaults;
import com.hcsy.spring.common.constants.HttpCode;
import com.hcsy.spring.common.constants.Messages;
import com.hcsy.spring.common.utils.Result;
import com.hcsy.spring.common.utils.SimpleLogger;
import com.hcsy.spring.infra.client.FastAPIClient;
import com.hcsy.spring.infra.client.GoZeroClient;

import lombok.RequiredArgsConstructor;
import reactor.core.publisher.Mono;
import reactor.util.retry.Retry;

@Service
@RequiredArgsConstructor
public class AsyncSyncServiceImpl implements AsyncSyncService {

    private static final int MAX_RETRY_TIMES = 3;
    private static final Duration RETRY_DELAY = Duration.ofSeconds(1);

    private final GoZeroClient goZeroClient;
    private final FastAPIClient fastAPIClient;
    private final SimpleLogger logger;

    @Override
    public Mono<Void> syncAllAsync(Long userId, String username) {
        String user = (username != null ? username : Defaults.DEFAULT_USER) + ":"
                + (userId != null ? userId : Defaults.DEFAULT_USER_ID);
        long startTime = System.currentTimeMillis();
        logger.info(user + Messages.SYNC);

        Mono<Void> es = reactiveCall(goZeroClient::syncES, Messages.SYNC_ES_SUCCESS);
        Mono<Void> vector = reactiveCall(fastAPIClient::syncVector, Messages.SYNC_VECTOR_SUCCESS);
        Mono<Void> cache = reactiveCall(fastAPIClient::clearAnalyzeCaches, Messages.CLEAR_CACHE_SUCCESS);

        return Mono.when(es, vector, cache)
                .doOnSuccess(ignored -> {
                    long duration = System.currentTimeMillis() - startTime;
                    logger.info(Messages.SYNC_PARALLEL_SUCCESS, user, duration);
                    logger.info(Messages.SYNC_ALL_SUCCESS);
                })
                .doOnError(error -> {
                    long duration = System.currentTimeMillis() - startTime;
                    logger.error(Messages.SYNC_PARALLEL_FAIL, user, duration, error.getMessage(), error);
                });
    }

    private Mono<Void> reactiveCall(Supplier<Mono<Result<?>>> action, String successMessage) {
        return Mono.defer(action)
                .flatMap(result -> result.getCode() != null && result.getCode() == HttpCode.OK
                        ? Mono.empty()
                        : Mono.error(new IllegalStateException(result.getMsg())))
                .retryWhen(Retry.fixedDelay(MAX_RETRY_TIMES, RETRY_DELAY)
                        .doBeforeRetry(signal -> logger.warning(Messages.SYNC_TASK_RETRY,
                                signal.totalRetries() + 1, signal.failure().getMessage())))
                .doOnSuccess(ignored -> logger.info(successMessage))
                .then();
    }
}

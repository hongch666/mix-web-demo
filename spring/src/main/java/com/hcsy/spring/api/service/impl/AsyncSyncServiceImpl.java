package com.hcsy.spring.api.service.impl;

import java.util.ArrayList;
import java.util.List;
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

@Service
@RequiredArgsConstructor
public class AsyncSyncServiceImpl implements AsyncSyncService {

    private final GoZeroClient goZeroClient;
    private final FastAPIClient fastAPIClient;
    private final SimpleLogger logger;

    @Override
    public Mono<Void> syncAllAsync(Long userId, String username, boolean syncES, boolean syncVector) {
        // 重试与熔断统一由底层 ServiceWebClient 的 resilience4j 处理，此处不再叠加重试，避免重复重试放大调用次数与耗时
        // 数仓同步承载浏览、点赞、收藏、关注等统计口径，任一变更都要执行
        List<Mono<Void>> tasks = new ArrayList<>();
        if (syncES) {
            tasks.add(reactiveCall(goZeroClient::syncES, Messages.SYNC_ES_SUCCESS));
        }
        if (syncVector) {
            tasks.add(reactiveCall(fastAPIClient::syncVector, Messages.SYNC_VECTOR_SUCCESS));
        }
        tasks.add(warehouseTask());

        return execute(userId, username, buildSyncTargets(syncES, syncVector), Mono.when(tasks));
    }

    @Override
    public Mono<Void> syncWarehouseAsync(Long userId, String username) {
        return execute(userId, username, Messages.SYNC_TARGET_WAREHOUSE, warehouseTask());
    }

    private Mono<Void> warehouseTask() {
        return reactiveCall(fastAPIClient::syncWarehouse, Messages.WAREHOUSE_SYNC_SUCCESS);
    }

    @Override
    public Mono<Void> syncNeo4jAsync(String methodName, String description) {
        return fastAPIClient.syncNeo4j()
            .doOnSubscribe(ignored -> logger.info(Messages.NEO4J_SYNC_TASK_START_MESSAGE, methodName, description))
            .doOnNext(response -> logNeo4jResponse(response, methodName, description))
            .doOnError(error -> logger.error(Messages.NEO4J_SYNC_TASK_SUBMIT_FAIL_MESSAGE,
                methodName, description, error.getMessage(), error))
            .onErrorResume(error -> Mono.empty())
            .then();
    }

    /**
     * 记录 Neo4j 同步接口的响应结果
     */
    private void logNeo4jResponse(Result<?> response, String methodName, String description) {
        if (response == null) {
            logger.warning(Messages.NEO4J_SYNC_CALL_EMPTY_MESSAGE, methodName, description);
        } else if (response.getCode() == null || response.getCode() != HttpCode.OK) {
            logger.warning(Messages.NEO4J_SYNC_CALL_FAIL_MESSAGE, methodName, description, response.getMsg());
        } else {
            logger.info(Messages.NEO4J_SYNC_TASK_SUBMIT_SUCCESS_MESSAGE, methodName, description);
        }
    }

    /**
     * 统一的同步执行与日志出口
     */
    private Mono<Void> execute(Long userId, String username, String targets, Mono<Void> sync) {
        String user = (username != null ? username : Defaults.DEFAULT_USER) + ":"
            + (userId != null ? userId : Defaults.DEFAULT_USER_ID);
        long startTime = System.currentTimeMillis();
        logger.info(user + String.format(Messages.SYNC_TARGETS, targets));

        return sync
            .doOnSuccess(ignored -> logger.info(Messages.SYNC_SUCCESS, user, System.currentTimeMillis() - startTime))
            .doOnError(error -> logger.error(Messages.SYNC_FAIL, user,
                System.currentTimeMillis() - startTime, error.getMessage(), error));
    }

    /**
     * 拼装本次实际触发的同步目标，用于日志区分跳过的目标
     */
    private String buildSyncTargets(boolean syncES, boolean syncVector) {
        List<String> targets = new ArrayList<>();
        if (syncES) {
            targets.add(Messages.SYNC_TARGET_ES);
        }
        if (syncVector) {
            targets.add(Messages.SYNC_TARGET_VECTOR);
        }
        targets.add(Messages.SYNC_TARGET_WAREHOUSE);
        return String.join("、", targets);
    }

    private Mono<Void> reactiveCall(Supplier<Mono<Result<?>>> action, String successMessage) {
        return Mono.defer(action)
            .flatMap(result -> result.getCode() != null && result.getCode() == HttpCode.OK
                ? Mono.empty()
                : Mono.error(new IllegalStateException(result.getMsg())))
            .doOnSuccess(ignored -> logger.info(successMessage))
            .then();
    }
}

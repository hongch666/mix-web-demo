package com.hcsy.spring.application.service.impl;

import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import java.util.function.Supplier;

import org.springframework.stereotype.Service;

import com.hcsy.spring.application.service.AsyncSyncService;
import com.hcsy.spring.common.constants.Defaults;
import com.hcsy.spring.common.constants.HttpCode;
import com.hcsy.spring.common.constants.Messages;
import com.hcsy.spring.common.utils.Result;
import com.hcsy.spring.common.utils.SimpleLogger;
import com.hcsy.spring.entity.event.ChangeEvent;
import com.hcsy.spring.infra.client.FastAPIClient;
import com.hcsy.spring.infra.client.GoZeroClient;

import lombok.RequiredArgsConstructor;
import reactor.core.publisher.Mono;

/**
 * AsyncSyncService 的实现，在数据变更后按需异步调用 go-zero 服务同步 ES、FastAPI 同步向量库与数仓并提交 Neo4j 同步事件
 */
@Service
@RequiredArgsConstructor
public class AsyncSyncServiceImpl implements AsyncSyncService {

    private final GoZeroClient goZeroClient;
    private final FastAPIClient fastAPIClient;
    private final SimpleLogger logger;

    /**
     * 实现文章变更后异步同步ES、向量库与数仓，按需跳过目标
     */
    @Override
    public Mono<Void> syncArticleAsync(Long userId, String username, boolean syncES, boolean syncVector,
        ChangeEvent event) {
        // 重试与熔断统一由底层 ServiceWebClient 的 resilience4j 处理，此处不再叠加重试，避免重复重试放大调用次数与耗时
        // 数仓同步承载浏览、点赞、收藏、关注等统计口径，任一变更都要执行，但只需刷新本次变更涉及的源表
        List<Mono<Void>> tasks = new ArrayList<>();
        if (syncES) {
            tasks.add(reactiveCall(() -> goZeroClient.syncES(event), Messages.SYNC_ES_SUCCESS));
        }
        if (syncVector) {
            tasks.add(reactiveCall(() -> fastAPIClient.syncVector(event), Messages.SYNC_VECTOR_SUCCESS));
        }
        tasks.add(warehouseTask(Set.of(event.getResource())));

        return execute(userId, username, buildSyncTargets(syncES, syncVector), Mono.when(tasks));
    }

    /**
     * 实现按资源类型异步同步数仓统计口径
     */
    @Override
    public Mono<Void> syncWarehouseAsync(Long userId, String username, Set<String> resources) {
        return execute(userId, username, Messages.SYNC_TARGET_WAREHOUSE, warehouseTask(resources));
    }

    /**
     * 构造数仓同步任务，响应码非成功时转为错误
     */
    private Mono<Void> warehouseTask(Set<String> resources) {
        return reactiveCall(() -> fastAPIClient.syncWarehouse(resources), Messages.WAREHOUSE_SYNC_SUCCESS);
    }

    /**
     * 实现向FastAPI提交Neo4j同步事件并记录响应与失败日志
     */
    @Override
    public Mono<Void> syncNeo4jAsync(String methodName, String description, ChangeEvent event) {
        return fastAPIClient.syncNeo4j(List.of(event))
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

    /**
     * 执行响应式同步调用，响应码非成功时转为错误并记录成功日志
     */
    private Mono<Void> reactiveCall(Supplier<Mono<Result<?>>> action, String successMessage) {
        return Mono.defer(action)
            .flatMap(result -> result.getCode() != null && result.getCode() == HttpCode.OK
                ? Mono.empty()
                : Mono.error(new IllegalStateException(result.getMsg())))
            .doOnSuccess(ignored -> logger.info(successMessage))
            .then();
    }
}

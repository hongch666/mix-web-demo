package com.hcsy.spring.api.service;

import reactor.core.publisher.Mono;

/**
 * 异步同步服务接口
 * 用于在后台异步执行 Neo4j 图谱、ES、向量库和 ClickHouse 数仓同步操作
 */
public interface AsyncSyncService {

    /**
     * 异步同步 ES、向量库和 ClickHouse 数仓
     * 此方法会在后台线程池中执行，不阻塞主流程
     *
     * @param userId
     *                       触发同步的用户ID（用于日志记录）
     * @param username
     *                       触发同步的用户名（用于日志记录）
     * @param syncES
     *                       是否同步 ES，仅文章文档发生变更的操作传 true
     * @param syncVector
     *                       是否同步向量库，仅文章内容可能变更的操作传 true
     */
    Mono<Void> syncAllAsync(Long userId, String username, boolean syncES, boolean syncVector);

    /**
     * 异步同步 ClickHouse 数仓
     * 供非文章类的写操作使用，用户、评论、分类等变更只需刷新数仓统计口径
     *
     * @param userId
     *                     触发同步的用户ID（用于日志记录）
     * @param username
     *                     触发同步的用户名（用于日志记录）
     */
    Mono<Void> syncWarehouseAsync(Long userId, String username);

    /**
     * 异步同步 Neo4j 知识图谱
     * 此方法会在后台线程池中执行，不阻塞主流程，失败只记日志
     *
     * @param methodName
     *                        触发同步的方法名（用于日志记录）
     * @param description
     *                        触发同步的操作描述（用于日志记录）
     */
    Mono<Void> syncNeo4jAsync(String methodName, String description);

}

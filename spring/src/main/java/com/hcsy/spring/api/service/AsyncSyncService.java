package com.hcsy.spring.api.service;

import java.util.Set;

import com.hcsy.spring.entity.event.ChangeEvent;

import reactor.core.publisher.Mono;

/**
 * 异步同步服务接口
 * 用于在后台异步执行 Neo4j 图谱、ES、向量库和 ClickHouse 数仓同步操作
 * 同步入参统一为变更事件，携带表名、主键与变更类型，实现精确同步
 */
public interface AsyncSyncService {

    /**
     * 异步同步文章链路：ES、向量库与 ClickHouse 数仓
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
     * @param event
     *                       变更事件，携带资源名、变更类型与受影响主键
     */
    Mono<Void> syncArticleAsync(Long userId, String username, boolean syncES, boolean syncVector, ChangeEvent event);

    /**
     * 异步同步 ClickHouse 数仓
     * 供非文章类的写操作使用，按资源名精确定位需要刷新的源表
     *
     * @param userId
     *                      触发同步的用户ID（用于日志记录）
     * @param username
     *                      触发同步的用户名（用于日志记录）
     * @param resources
     *                      本次变更涉及的源表资源名集合
     */
    Mono<Void> syncWarehouseAsync(Long userId, String username, Set<String> resources);

    /**
     * 异步同步 Neo4j 知识图谱
     * 此方法会在后台线程池中执行，不阻塞主流程，失败只记日志
     *
     * @param methodName
     *                        触发同步的方法名（用于日志记录）
     * @param description
     *                        触发同步的操作描述（用于日志记录）
     * @param event
     *                        变更事件，携带资源名、变更类型与受影响主键
     */
    Mono<Void> syncNeo4jAsync(String methodName, String description, ChangeEvent event);

}

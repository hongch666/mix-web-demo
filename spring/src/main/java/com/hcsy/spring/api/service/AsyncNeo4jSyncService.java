package com.hcsy.spring.api.service;

/**
 * Neo4j 异步同步服务接口
 * 用于在后台异步执行知识图谱同步操作
 */
public interface AsyncNeo4jSyncService {

    /**
     * 异步同步 Neo4j
     * 此方法会在后台线程池中执行，不阻塞主流程
     *
     * @param methodName  触发同步的方法名
     * @param description 触发同步的操作描述
     */
    void syncNeo4jAsync(String methodName, String description);
}

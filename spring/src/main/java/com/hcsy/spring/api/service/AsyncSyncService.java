package com.hcsy.spring.api.service;

/**
 * 异步同步服务接口
 * 用于在后台异步执行 ES、Hive、Vector 同步操作
 */
public interface AsyncSyncService {

    /**
     * 异步同步 ES、Hive 和 Vector
     * 此方法会在后台线程池中执行，不阻塞主流程
     * 
     * @param userId   触发同步的用户ID（用于日志记录）
     * @param username 触发同步的用户名（用于日志记录）
     */
    void syncAllAsync(Long userId, String username);
}

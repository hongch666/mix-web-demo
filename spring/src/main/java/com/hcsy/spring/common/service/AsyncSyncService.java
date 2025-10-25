package com.hcsy.spring.common.service;

import com.hcsy.spring.common.client.FastAPIClient;
import com.hcsy.spring.common.client.GinClient;
import com.hcsy.spring.common.utils.SimpleLogger;
import com.hcsy.spring.common.utils.UserContext;
import lombok.RequiredArgsConstructor;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;

/**
 * 异步同步服务
 * 用于在后台异步执行 ES、Hive、Vector 同步操作
 */
@Service
@RequiredArgsConstructor
public class AsyncSyncService {

    private final GinClient ginClient;
    private final FastAPIClient fastAPIClient;
    private final SimpleLogger logger;

    /**
     * 异步同步 ES、Hive 和 Vector
     * 此方法会在后台线程池中执行，不阻塞主流程
     * 
     * @param userId   触发同步的用户ID（用于日志记录）
     * @param username 触发同步的用户名（用于日志记录）
     */
    @Async("asyncExecutor")
    public void syncAllAsync(Long userId, String username) {
        try {
            logger.info("[异步任务] 用户 " + (username != null ? username : "unknown") + "(ID:"
                    + (userId != null ? userId : "null") + ") 触发同步 ES、Hive 和 Vector...");

            // 同步 ES
            try {
                ginClient.syncES();
                logger.info("[异步任务] ES 同步完成");
            } catch (Exception e) {
                logger.error("[异步任务] ES 同步失败: " + e.getMessage(), e);
            }

            // 同步 Hive
            try {
                fastAPIClient.syncHive();
                logger.info("[异步任务] Hive 同步完成");
            } catch (Exception e) {
                logger.error("[异步任务] Hive 同步失败: " + e.getMessage(), e);
            }

            // 同步 Vector
            try {
                fastAPIClient.syncVector();
                logger.info("[异步任务] Vector 同步完成");
            } catch (Exception e) {
                logger.error("[异步任务] Vector 同步失败: " + e.getMessage(), e);
            }

            logger.info("[异步任务] 所有同步任务执行完毕");
        } catch (Exception e) {
            logger.error("[异步任务] 同步过程发生未知异常: " + e.getMessage(), e);
        } finally {
            // ✓ 清理 ThreadLocal，避免线程池复用时污染
            UserContext.clear();
            logger.debug("[异步任务] UserContext 已清理");
        }
    }
}

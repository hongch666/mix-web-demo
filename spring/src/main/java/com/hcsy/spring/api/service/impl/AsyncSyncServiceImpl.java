package com.hcsy.spring.api.service.impl;

import com.hcsy.spring.api.service.AsyncSyncService;
import com.hcsy.spring.common.client.FastAPIClient;
import com.hcsy.spring.common.client.GinClient;
import com.hcsy.spring.common.utils.Constants;
import com.hcsy.spring.common.utils.SimpleLogger;
import com.hcsy.spring.common.utils.UserContext;
import lombok.RequiredArgsConstructor;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * 异步同步服务实现
 * 用于在后台异步执行 ES、Hive、Vector 同步操作
 */
@Service
@RequiredArgsConstructor
@Transactional
public class AsyncSyncServiceImpl implements AsyncSyncService {

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
    @Override
    @Async("asyncExecutor")
    public void syncAllAsync(Long userId, String username) {
        try {
            logger.info(
                (username != null ? username : Constants.DEFAULT_USER) + 
                ":"+ 
                (userId != null ? userId : Constants.DEFAULT_USER_ID) + 
                Constants.SYNC
            );

            // 同步 ES
            try {
                ginClient.syncES();
                logger.info(Constants.SYNC_ES_SUCCESS);
            } catch (Exception e) {
                logger.error(Constants.SYNC_ES_FAIL + e.getMessage(), e);
            }

            // 同步 Hive
            try {
                fastAPIClient.syncHive();
                logger.info(Constants.SYNC_HIVE_SUCCESS);
            } catch (Exception e) {
                logger.error(Constants.SYNC_HIVE_FAIL + e.getMessage(), e);
            }

            // 同步 Vector
            try {
                fastAPIClient.syncVector();
                logger.info(Constants.SYNC_VECTOR_SUCCESS);
            } catch (Exception e) {
                logger.error(Constants.SYNC_VECTOR_FAIL + e.getMessage(), e);
            }

            logger.info(Constants.SYNC_ALL_SUCCESS);
        } catch (Exception e) {
            logger.error(Constants.SYNC_ALL_FAIL + e.getMessage(), e);
        } finally {
            // 清理 ThreadLocal，避免线程池复用时污染
            UserContext.clear();
            logger.debug(Constants.CLEAN_CONTEXT);
        }
    }

    /**
     * 异步同步 Hive 只
     * 此方法会在后台线程池中执行，不阻塞主流程
     * 仅同步 Hive，不同步 ES 和 Vector（用于浏览量更新等轻量级操作）
     * 
     * @param userId   触发同步的用户ID（用于日志记录）
     * @param username 触发同步的用户名（用于日志记录）
     */
    @Override
    @Async("asyncExecutor")
    public void syncHiveOnlyAsync(Long userId, String username) {
        try {
            logger.info(
                (username != null ? username : "unknown") + 
                ":"+ 
                (userId != null ? userId : "null") + 
                Constants.SYNC_HIVE
            );

            // 仅同步 Hive
            try {
                fastAPIClient.syncHive();
                logger.info(Constants.SYNC_HIVE_SUCCESS);
            } catch (Exception e) {
                logger.error(Constants.SYNC_HIVE_FAIL + e.getMessage(), e);
            }

            logger.info(Constants.SYNC_ALL_SUCCESS);
        } catch (Exception e) {
            logger.error(Constants.SYNC_ALL_FAIL + e.getMessage(), e);
        } finally {
            // 清理 ThreadLocal，避免线程池复用时污染
            UserContext.clear();
            logger.debug(Constants.CLEAN_CONTEXT);
        }
    }
}

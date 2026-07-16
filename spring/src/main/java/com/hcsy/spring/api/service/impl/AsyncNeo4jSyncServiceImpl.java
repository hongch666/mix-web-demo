package com.hcsy.spring.api.service.impl;

import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;

import com.hcsy.spring.api.service.AsyncNeo4jSyncService;
import com.hcsy.spring.common.constants.Messages;
import com.hcsy.spring.common.constants.HttpCode;
import com.hcsy.spring.common.utils.Result;
import com.hcsy.spring.common.utils.SimpleLogger;
import com.hcsy.spring.infra.client.FastAPIClient;
import com.hcsy.spring.infra.client.GoZeroClient;

import lombok.RequiredArgsConstructor;

/**
 * Neo4j 异步同步服务实现
 */
@Service
@RequiredArgsConstructor
public class AsyncNeo4jSyncServiceImpl implements AsyncNeo4jSyncService {

    private final FastAPIClient fastAPIClient;
    private final GoZeroClient goZeroClient;
    private final SimpleLogger logger;

    @Override
    @Async("syncTaskExecutor")
    public void syncNeo4jAsync(String methodName, String description) {
        logger.info(Messages.NEO4J_SYNC_TASK_START_MESSAGE, methodName, description);

        // 1. 触发 Neo4j 同步 (MySQL → Neo4j, Agent 使用, 保留)
        try {
            Result<?> response = fastAPIClient.syncNeo4j();
            if (response != null && response.getCode() == HttpCode.OK) {
                logger.info(Messages.NEO4J_SYNC_TASK_SUBMIT_SUCCESS_MESSAGE, methodName, description);
            } else if (response != null) {
                logger.warning(Messages.NEO4J_SYNC_CALL_FAIL_MESSAGE, methodName, description, response.getMsg());
            }
        } catch (Exception e) {
            logger.error(Messages.NEO4J_SYNC_TASK_SUBMIT_FAIL_MESSAGE, methodName, description, e.getMessage(), e);
        }

        // 2. 触发图谱缓存刷新 (Neo4j → Redis, 新增)
        //    异步触发, 失败不阻塞主流程
        try {
            goZeroClient.syncGraphCache();
        } catch (Exception e) {
            logger.warning(Messages.SYNC_GRAPH_CACHE_WARN + e.getMessage());
        }
    }
}

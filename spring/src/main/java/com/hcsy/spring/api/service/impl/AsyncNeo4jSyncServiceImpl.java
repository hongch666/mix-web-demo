package com.hcsy.spring.api.service.impl;

import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;

import com.hcsy.spring.api.service.AsyncNeo4jSyncService;
import com.hcsy.spring.common.utils.Constants;
import com.hcsy.spring.common.utils.HttpCode;
import com.hcsy.spring.common.utils.Result;
import com.hcsy.spring.common.utils.SimpleLogger;
import com.hcsy.spring.infra.client.FastAPIClient;

import lombok.RequiredArgsConstructor;

/**
 * Neo4j 异步同步服务实现
 */
@Service
@RequiredArgsConstructor
public class AsyncNeo4jSyncServiceImpl implements AsyncNeo4jSyncService {

    private final FastAPIClient fastAPIClient;
    private final SimpleLogger logger;

    @Override
    @Async("asyncExecutor")
    public void syncNeo4jAsync(String methodName, String description) {
        logger.info(Constants.NEO4J_SYNC_TASK_START_MESSAGE, methodName, description);

        try {
            Result<?> response = fastAPIClient.syncNeo4j();
            if (response == null) {
                logger.warning(Constants.NEO4J_SYNC_CALL_EMPTY_MESSAGE, methodName, description);
                return;
            }

            if (response.getCode() != HttpCode.OK) {
                logger.warning(Constants.NEO4J_SYNC_CALL_FAIL_MESSAGE, methodName, description, response.getMsg());
                return;
            }

            logger.info(Constants.NEO4J_SYNC_TASK_SUBMIT_SUCCESS_MESSAGE, methodName, description);
        } catch (Exception e) {
            logger.error(Constants.NEO4J_SYNC_TASK_SUBMIT_FAIL_MESSAGE, methodName, description, e.getMessage(), e);
        }
    }
}

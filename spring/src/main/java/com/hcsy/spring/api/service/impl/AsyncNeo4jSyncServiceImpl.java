package com.hcsy.spring.api.service.impl;

import org.springframework.stereotype.Service;

import com.hcsy.spring.api.service.AsyncNeo4jSyncService;
import com.hcsy.spring.common.constants.HttpCode;
import com.hcsy.spring.common.constants.Messages;
import com.hcsy.spring.common.utils.Result;
import com.hcsy.spring.common.utils.SimpleLogger;
import com.hcsy.spring.infra.client.FastAPIClient;

import lombok.RequiredArgsConstructor;
import reactor.core.publisher.Mono;

@Service
@RequiredArgsConstructor
public class AsyncNeo4jSyncServiceImpl implements AsyncNeo4jSyncService {

    private final FastAPIClient fastAPIClient;
    private final SimpleLogger logger;

    @Override
    public Mono<Void> syncNeo4jAsync(String methodName, String description) {
        return fastAPIClient.syncNeo4j()
                .doOnSubscribe(ignored -> logger.info(Messages.NEO4J_SYNC_TASK_START_MESSAGE, methodName, description))
                .doOnNext(response -> logResponse(response, methodName, description))
                .doOnError(error -> logger.error(Messages.NEO4J_SYNC_TASK_SUBMIT_FAIL_MESSAGE,
                        methodName, description, error.getMessage(), error))
                .onErrorResume(error -> Mono.empty())
                .then();
    }

    private void logResponse(Result<?> response, String methodName, String description) {
        if (response == null) {
            logger.warning(Messages.NEO4J_SYNC_CALL_EMPTY_MESSAGE, methodName, description);
        } else if (response.getCode() != HttpCode.OK) {
            logger.warning(Messages.NEO4J_SYNC_CALL_FAIL_MESSAGE, methodName, description, response.getMsg());
        } else {
            logger.info(Messages.NEO4J_SYNC_TASK_SUBMIT_SUCCESS_MESSAGE, methodName, description);
        }
    }
}

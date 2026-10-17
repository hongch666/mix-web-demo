package com.hcsy.spring.application.service.impl;

import org.springframework.stereotype.Service;

import com.hcsy.spring.application.service.AsyncApiLogService;
import com.hcsy.spring.common.constants.Messages;
import com.hcsy.spring.common.constants.RabbitQueues;
import com.hcsy.spring.common.utils.RabbitMQUtil;
import com.hcsy.spring.common.utils.SimpleLogger;
import com.hcsy.spring.entity.event.ApiLogEvent;

import lombok.RequiredArgsConstructor;
import reactor.core.publisher.Mono;

@Service
@RequiredArgsConstructor
public class AsyncApiLogServiceImpl implements AsyncApiLogService {

    private final RabbitMQUtil rabbitMQUtil;
    private final SimpleLogger logger;

    @Override
    public Mono<Void> sendAsync(ApiLogEvent apiLogEvent) {
        return rabbitMQUtil.sendMessage(RabbitQueues.API_LOG, apiLogEvent)
            .doOnSuccess(ignored -> logger.info(Messages.ASYNC_API_LOG_SEND_SUCCESS))
            .doOnError(error -> logger.error(Messages.ASYNC_API_LOG_SEND_FAILED, error.getMessage(), error))
            .onErrorResume(error -> Mono.empty());
    }
}

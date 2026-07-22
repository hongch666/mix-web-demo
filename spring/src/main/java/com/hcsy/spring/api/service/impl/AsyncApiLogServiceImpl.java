package com.hcsy.spring.api.service.impl;

import java.util.Map;

import org.springframework.stereotype.Service;

import com.hcsy.spring.api.service.AsyncApiLogService;
import com.hcsy.spring.common.constants.Messages;
import com.hcsy.spring.common.utils.RabbitMQUtil;
import com.hcsy.spring.common.utils.SimpleLogger;

import lombok.RequiredArgsConstructor;
import reactor.core.publisher.Mono;

@Service
@RequiredArgsConstructor
public class AsyncApiLogServiceImpl implements AsyncApiLogService {

    private final RabbitMQUtil rabbitMQUtil;
    private final SimpleLogger logger;

    @Override
    public Mono<Void> sendAsync(Map<String, Object> apiLogMessage) {
        return rabbitMQUtil.sendMessage("api-log-queue", apiLogMessage)
                .doOnSuccess(ignored -> logger.info(Messages.ASYNC_API_LOG_SEND_SUCCESS))
                .doOnError(error -> logger.error(Messages.ASYNC_API_LOG_SEND_FAILED, error.getMessage(), error))
                .onErrorResume(error -> Mono.empty());
    }
}

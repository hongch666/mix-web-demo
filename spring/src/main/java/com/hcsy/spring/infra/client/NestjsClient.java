package com.hcsy.spring.infra.client;

import java.time.Duration;

import org.springframework.http.HttpMethod;
import org.springframework.stereotype.Component;

import com.hcsy.spring.common.constants.Messages;
import com.hcsy.spring.common.utils.Result;
import com.hcsy.spring.entity.dto.InternalEmailCodeSendDTO;

import lombok.RequiredArgsConstructor;
import reactor.core.publisher.Mono;

@Component
@RequiredArgsConstructor
public class NestjsClient {

    private final ServiceWebClient serviceWebClient;

    public Mono<Result<?>> sendEmailCode(InternalEmailCodeSendDTO dto) {
        ServiceRequestOptions options = ServiceRequestOptions.builder()
                .body(dto)
                .build();
        return serviceWebClient.request(HttpMethod.POST, "nestjs", "/email/send-code", options, Duration.ofSeconds(3),
                Messages.NESTJS_EMAIL_SERVICE_UNAVAILABLE_MSG);
    }
}

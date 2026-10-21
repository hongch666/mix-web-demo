package com.hcsy.spring.infra.client;

import org.springframework.http.HttpMethod;
import org.springframework.stereotype.Component;

import com.hcsy.spring.common.constants.Messages;
import com.hcsy.spring.common.utils.Result;
import com.hcsy.spring.entity.dto.InternalEmailCodeSendDTO;

import lombok.RequiredArgsConstructor;
import reactor.core.publisher.Mono;

/**
 * 封装对 NestJS 服务的调用，通过邮件接口发送验证码邮件
 */
@Component
@RequiredArgsConstructor
public class NestjsClient {

    private final ServiceWebClient serviceWebClient;

    /**
     * 调用 NestJS 服务的邮件接口发送验证码邮件
     */
    public Mono<Result<?>> sendEmailCode(InternalEmailCodeSendDTO dto) {
        ServiceRequestOptions options = ServiceRequestOptions.builder()
            .body(dto)
            .build();
        return serviceWebClient.request(HttpMethod.POST, "nestjs", "/email/send-code", options,
            Messages.NESTJS_EMAIL_SERVICE_UNAVAILABLE_MSG);
    }
}

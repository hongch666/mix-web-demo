package com.hcsy.spring.infra.client.fallback;

import org.springframework.cloud.openfeign.FallbackFactory;
import org.springframework.stereotype.Component;

import com.hcsy.spring.common.constants.Messages;
import com.hcsy.spring.common.constants.HttpCode;
import com.hcsy.spring.common.utils.Result;
import com.hcsy.spring.common.utils.SimpleLogger;
import com.hcsy.spring.entity.dto.InternalEmailCodeSendDTO;
import com.hcsy.spring.infra.client.NestjsClient;

import lombok.RequiredArgsConstructor;

@Component
@RequiredArgsConstructor
public class NestjsClientFallbackFactory implements FallbackFactory<NestjsClient> {

    private final SimpleLogger logger;

    @Override
    public NestjsClient create(Throwable cause) {
        logger.error(Messages.NESTJS_SERVICE_UNAVAILABLE + cause.getMessage(), cause);

        return new NestjsClient() {
            @Override
            public Result<?> testNestjs() {
                return Result.error(HttpCode.SERVICE_UNAVAILABLE, Messages.NESTJS_SERVICE_UNAVAILABLE_DEGRADE);
            }

            @Override
            public Result<?> sendEmailCode(InternalEmailCodeSendDTO dto) {
                logger.error(Messages.NESTJS_EMAIL_SERVICE_UNAVAILABLE + cause.getMessage(), cause);
                return Result.error(HttpCode.SERVICE_UNAVAILABLE, Messages.NESTJS_EMAIL_SERVICE_UNAVAILABLE_MSG);
            }
        };
    }
}

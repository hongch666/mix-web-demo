package com.hcsy.spring.infra.client.fallback;

import org.springframework.cloud.openfeign.FallbackFactory;
import org.springframework.stereotype.Component;

import com.hcsy.spring.common.utils.Result;
import com.hcsy.spring.common.utils.SimpleLogger;
import com.hcsy.spring.infra.client.NestjsClient;

import lombok.RequiredArgsConstructor;

@Component
@RequiredArgsConstructor
public class NestjsClientFallbackFactory implements FallbackFactory<NestjsClient> {

    private final SimpleLogger logger;

    @Override
    public NestjsClient create(Throwable cause) {
        logger.error("NestJS 服务调用触发降级: " + cause.getMessage(), cause);

        return new NestjsClient() {
            @Override
            public Result testNestjs() {
                return Result.error("NestJS 服务暂时不可用，已触发降级");
            }
        };
    }
}

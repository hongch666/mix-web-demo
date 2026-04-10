package com.hcsy.spring.infra.client.fallback;

import org.springframework.cloud.openfeign.FallbackFactory;
import org.springframework.stereotype.Component;

import com.hcsy.spring.common.utils.Result;
import com.hcsy.spring.common.utils.SimpleLogger;
import com.hcsy.spring.infra.client.GoZeroClient;

import lombok.RequiredArgsConstructor;

@Component
@RequiredArgsConstructor
public class GoZeroClientFallbackFactory implements FallbackFactory<GoZeroClient> {

    private final SimpleLogger logger;

    @Override
    public GoZeroClient create(Throwable cause) {
        logger.error("GoZero 服务调用触发降级: " + cause.getMessage(), cause);

        return new GoZeroClient() {
            @Override
            public Result testGoZero() {
                return Result.error("GoZero 服务暂时不可用，已触发降级");
            }

            @Override
            public Result syncES() {
                return Result.error("ES 同步服务暂时不可用，已触发降级");
            }
        };
    }
}

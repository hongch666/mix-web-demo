package com.hcsy.spring.infra.client.fallback;

import org.springframework.cloud.openfeign.FallbackFactory;
import org.springframework.stereotype.Component;

import com.hcsy.spring.common.utils.Constants;
import com.hcsy.spring.common.utils.HttpCode;
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
        logger.error(Constants.GOZERO_SERVICE_UNAVAILABLE + cause.getMessage(), cause);

        return new GoZeroClient() {
            @Override
            public Result<?> testGoZero() {
                return Result.error(HttpCode.SERVICE_UNAVAILABLE, Constants.GOZERO_SERVICE_UNAVAILABLE_DEGRADE);
            }

            @Override
            public Result<?> syncES() {
                return Result.error(HttpCode.SERVICE_UNAVAILABLE, Constants.ES_SERVICE_UNAVAILABLE);
            }
        };
    }
}

package com.hcsy.spring.infra.client.fallback;

import org.springframework.cloud.openfeign.FallbackFactory;
import org.springframework.stereotype.Component;

import com.hcsy.spring.common.constants.Messages;
import com.hcsy.spring.common.constants.HttpCode;
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
        logger.error(Messages.GOZERO_SERVICE_UNAVAILABLE + cause.getMessage(), cause);

        return new GoZeroClient() {
            @Override
            public Result<?> testGoZero() {
                return Result.error(HttpCode.SERVICE_UNAVAILABLE, Messages.GOZERO_SERVICE_UNAVAILABLE_DEGRADE);
            }

            @Override
            public Result<?> syncES() {
                return Result.error(HttpCode.SERVICE_UNAVAILABLE, Messages.ES_SERVICE_UNAVAILABLE);
            }
        };
    }
}

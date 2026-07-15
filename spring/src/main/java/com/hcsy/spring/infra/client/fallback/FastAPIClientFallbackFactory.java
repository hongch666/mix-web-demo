package com.hcsy.spring.infra.client.fallback;

import org.springframework.cloud.openfeign.FallbackFactory;
import org.springframework.stereotype.Component;

import com.hcsy.spring.common.constants.Messages;
import com.hcsy.spring.common.constants.HttpCode;
import com.hcsy.spring.common.utils.Result;
import com.hcsy.spring.common.utils.SimpleLogger;
import com.hcsy.spring.infra.client.FastAPIClient;

import lombok.RequiredArgsConstructor;

@Component
@RequiredArgsConstructor
public class FastAPIClientFallbackFactory implements FallbackFactory<FastAPIClient> {

    private final SimpleLogger logger;

    @Override
    public FastAPIClient create(Throwable cause) {
        logger.error(Messages.FASTAPI_CALL_DEGRADED + cause.getMessage(), cause);

        return new FastAPIClient() {
            @Override
            public Result<?> testFastAPI() {
                return Result.error(HttpCode.SERVICE_UNAVAILABLE, Messages.FASTAPI_SERVICE_UNAVAILABLE);
            }

            @Override
            public Result<?> syncVector() {
                return Result.error(HttpCode.SERVICE_UNAVAILABLE, Messages.VECTOR_SYNC_SERVICE_UNAVAILABLE);
            }

            @Override
            public Result<?> clearAnalyzeCaches() {
                return Result.error(HttpCode.SERVICE_UNAVAILABLE, Messages.ANALYSIS_CACHE_CLEANUP_SERVICE_UNAVAILABLE);
            }

            @Override
            public Result<?> syncNeo4j() {
                return Result.error(HttpCode.SERVICE_UNAVAILABLE, Messages.NEO4J_SYNC_SERVICE_UNAVAILABLE);
            }
        };
    }
}

package com.hcsy.spring.infra.client.fallback;

import org.springframework.cloud.openfeign.FallbackFactory;
import org.springframework.stereotype.Component;

import com.hcsy.spring.common.utils.Constants;
import com.hcsy.spring.common.utils.HttpCode;
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
        logger.error(Constants.FASTAPI_CALL_DEGRADED + cause.getMessage(), cause);

        return new FastAPIClient() {
            @Override
            public Result<?> testFastAPI() {
                return Result.error(HttpCode.SERVICE_UNAVAILABLE, Constants.FASTAPI_SERVICE_UNAVAILABLE);
            }

            @Override
            public Result<?> syncVector() {
                return Result.error(HttpCode.SERVICE_UNAVAILABLE, Constants.VECTOR_SYNC_SERVICE_UNAVAILABLE);
            }

            @Override
            public Result<?> clearAnalyzeCaches() {
                return Result.error(HttpCode.SERVICE_UNAVAILABLE, Constants.ANALYSIS_CACHE_CLEANUP_SERVICE_UNAVAILABLE);
            }

            @Override
            public Result<?> syncNeo4j() {
                return Result.error(HttpCode.SERVICE_UNAVAILABLE, Constants.NEO4J_SYNC_SERVICE_UNAVAILABLE);
            }
        };
    }
}

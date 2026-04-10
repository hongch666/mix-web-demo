package com.hcsy.spring.infra.client.fallback;

import org.springframework.cloud.openfeign.FallbackFactory;
import org.springframework.stereotype.Component;

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
        logger.error("FastAPI 服务调用触发降级: " + cause.getMessage(), cause);

        return new FastAPIClient() {
            @Override
            public Result testFastAPI() {
                return Result.error("FastAPI 服务暂时不可用，已触发降级");
            }

            @Override
            public Result syncVector() {
                return Result.error("向量同步服务暂时不可用，已触发降级");
            }

            @Override
            public Result clearAnalyzeCaches() {
                return Result.error("分析缓存清理服务暂时不可用，已触发降级");
            }
        };
    }
}

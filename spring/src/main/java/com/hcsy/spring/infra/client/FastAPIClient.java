package com.hcsy.spring.infra.client;

import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;

import com.hcsy.spring.common.utils.Result;
import com.hcsy.spring.infra.client.fallback.FastAPIClientFallbackFactory;

@FeignClient(name = "fastapi", fallbackFactory = FastAPIClientFallbackFactory.class)
public interface FastAPIClient {
    @GetMapping("/api_fastapi/fastapi")
    Result testFastAPI();

    @PostMapping("/api_fastapi/task/vector")
    Result syncVector();

    @PostMapping("/api_fastapi/task/clear-analyze-caches")
    Result clearAnalyzeCaches();
}

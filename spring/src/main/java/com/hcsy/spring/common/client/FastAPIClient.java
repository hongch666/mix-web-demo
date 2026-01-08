package com.hcsy.spring.common.client;

import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;

import com.hcsy.spring.common.utils.Result;

@FeignClient(name = "fastapi")
public interface FastAPIClient {
    @GetMapping("/api_fastapi/fastapi")
    Result testFastAPI();

    @PostMapping("/api_fastapi/task/hive")
    Result syncHive();

    @PostMapping("/api_fastapi/task/vector")
    Result syncVector();
}

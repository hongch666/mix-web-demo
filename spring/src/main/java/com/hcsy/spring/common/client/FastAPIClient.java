package com.hcsy.spring.common.client;

import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.GetMapping;

import com.hcsy.spring.entity.po.Result;

@FeignClient(name = "fastapi")
public interface FastAPIClient {
    @GetMapping("/api_fastapi/fastapi")
    Result testFastAPI();
}

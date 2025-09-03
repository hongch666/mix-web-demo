package com.hcsy.spring.common.client;

import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.PostMapping;

import com.hcsy.spring.entity.po.Result;

@FeignClient(name = "fastapi")
public interface FastAPIClient {
    @PostMapping("/api_fastapi/task")
    Result syncHive();
}

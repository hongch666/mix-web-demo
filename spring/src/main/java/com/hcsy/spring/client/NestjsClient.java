package com.hcsy.spring.client;

import com.hcsy.spring.po.Result;
import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.GetMapping;

@FeignClient(name = "nestjs")
public interface NestjsClient {
    @GetMapping("/api_nestjs/nestjs")
    Result testNestjs();
}

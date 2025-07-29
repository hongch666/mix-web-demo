package com.hcsy.spring.common.client;

import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.GetMapping;

import com.hcsy.spring.entity.po.Result;

@FeignClient(name = "nestjs")
public interface NestjsClient {
    @GetMapping("/api_nestjs/nestjs")
    Result testNestjs();
}

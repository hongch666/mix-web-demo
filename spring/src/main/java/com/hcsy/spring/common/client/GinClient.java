package com.hcsy.spring.common.client;

import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;

import com.hcsy.spring.entity.po.Result;

@FeignClient(name = "gin")
public interface GinClient {
    @GetMapping("/api_gin/gin")
    Result testGin();

    @PostMapping("/api_gin/syncer")
    Result syncES();
}

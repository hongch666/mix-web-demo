package com.hcsy.spring.common.client;

import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;

import com.hcsy.spring.common.utils.Result;

@FeignClient(name = "gozero")
public interface GoZeroClient {
    @GetMapping("/api_gozero/gin")
    Result testGin();

    @PostMapping("/api_gozero/syncer")
    Result syncES();
}

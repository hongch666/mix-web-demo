package com.hcsy.spring.infra.client;

import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;

import com.hcsy.spring.common.utils.Result;
import com.hcsy.spring.infra.client.fallback.GoZeroClientFallbackFactory;

@FeignClient(name = "gozero", fallbackFactory = GoZeroClientFallbackFactory.class)
public interface GoZeroClient {
    @GetMapping("/api_gozero/gozero")
    Result testGoZero();

    @PostMapping("/api_gozero/syncer")
    Result syncES();
}

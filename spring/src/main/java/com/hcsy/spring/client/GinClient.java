package com.hcsy.spring.client;

import com.hcsy.spring.po.Result;
import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;

@FeignClient(name = "gin")
public interface GinClient {
    @GetMapping("/api_gin/gin")
    Result testGin();

    @PostMapping("/api_gin/syncer")
    Result syncES();
}

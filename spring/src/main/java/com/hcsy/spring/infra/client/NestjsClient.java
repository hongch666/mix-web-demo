package com.hcsy.spring.infra.client;

import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;

import com.hcsy.spring.common.utils.Result;
import com.hcsy.spring.entity.dto.InternalEmailCodeSendDTO;
import com.hcsy.spring.infra.client.fallback.NestjsClientFallbackFactory;

@FeignClient(name = "nestjs", fallbackFactory = NestjsClientFallbackFactory.class)
public interface NestjsClient {

    @GetMapping("/api_nestjs/nestjs")
    Result testNestjs();

    @PostMapping("/email/send-code")
    Result sendEmailCode(@RequestBody InternalEmailCodeSendDTO dto);
}

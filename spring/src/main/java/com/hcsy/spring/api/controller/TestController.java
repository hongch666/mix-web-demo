package com.hcsy.spring.api.controller;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.hcsy.spring.common.constants.Defaults;
import com.hcsy.spring.common.utils.Result;
import com.hcsy.spring.core.annotation.ApiLog;
import com.hcsy.spring.infra.client.FastAPIClient;
import com.hcsy.spring.infra.client.GoZeroClient;
import com.hcsy.spring.infra.client.NestjsClient;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;

@RestController
@RequestMapping("/api_spring")
@RequiredArgsConstructor
@Tag(name = "测试模块", description = "服务测试相关API，用于验证各个微服务是否正常运行")
public class TestController {
    private final GoZeroClient goZeroClient;
    private final NestjsClient nestjsClient;
    private final FastAPIClient fastAPIClient;

    @GetMapping("/spring")
    @Operation(summary = "Spring自己的测试", description = "输出欢迎信息")
    @ApiLog("测试Spring服务")
    public Result<String> getHello() {
        return Result.success(Defaults.TEST);
    }

    @GetMapping("/gozero")
    @Operation(summary = "调用GoZero的测试", description = "输出欢迎信息")
    @ApiLog("测试GoZero服务")
    public Result<?> getGoZero() {
        return goZeroClient.testGoZero();
    }

    @GetMapping("/nestjs")
    @Operation(summary = "调用NestJS的测试", description = "输出欢迎信息")
    @ApiLog("测试NestJS服务")
    public Result<?> getNestjs() {
        return nestjsClient.testNestjs();
    }

    @GetMapping("/fastapi")
    @Operation(summary = "调用FastAPI的测试", description = "输出欢迎信息")
    @ApiLog("测试FastAPI服务")
    public Result<?> getFastAPI() {
        return fastAPIClient.testFastAPI();
    }
}

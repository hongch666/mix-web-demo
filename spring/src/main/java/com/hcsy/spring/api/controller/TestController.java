package com.hcsy.spring.api.controller;

import com.hcsy.spring.common.annotation.ApiLog;
import com.hcsy.spring.common.client.FastAPIClient;
import com.hcsy.spring.common.client.GinClient;
import com.hcsy.spring.common.client.NestjsClient;
import com.hcsy.spring.common.task.TokenCleanupTask;
import com.hcsy.spring.common.utils.Result;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api_spring")
@RequiredArgsConstructor
@Tag(name = "测试模块", description = "测试相关接口")
public class TestController {
    private final GinClient ginClient;
    private final NestjsClient nestjsClient;
    private final FastAPIClient fastAPIClient;
    private final TokenCleanupTask tokenCleanupTask;

    @GetMapping("/spring")
    @Operation(summary = "spring自己的测试", description = "输出欢迎信息")
    @ApiLog("测试Spring服务")
    public Result getHello() {
        return Result.success("Hello,I am Spring!");
    }

    @GetMapping("/gin")
    @Operation(summary = "调用Gin的测试", description = "输出欢迎信息")
    @ApiLog("测试Gin服务")
    public Result gerGin() {
        return ginClient.testGin();
    }

    @GetMapping("/nestjs")
    @Operation(summary = "调用NestJS的测试", description = "输出欢迎信息")
    @ApiLog("测试NestJS服务")
    public Result gerNestjs() {
        return nestjsClient.testNestjs();
    }

    @GetMapping("/fastapi")
    @Operation(summary = "调用FastAPI的测试", description = "输出欢迎信息")
    @ApiLog("测试FastAPI服务")
    public Result gerFastAPI() {
        return fastAPIClient.testFastAPI();
    }

    @PostMapping("/execute/clean")
    @Operation(summary = "手动执行清理过期Token", description = "手动触发清理过期Token任务")
    @ApiLog("手动执行清理过期Token任务")
    public Result executeTokenCleanup() {
        tokenCleanupTask.cleanupExpiredTokens();
        return Result.success();
    }
}

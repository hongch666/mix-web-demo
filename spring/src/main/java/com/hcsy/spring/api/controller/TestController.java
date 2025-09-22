package com.hcsy.spring.api.controller;

import com.hcsy.spring.common.annotation.ApiLog;
import com.hcsy.spring.common.client.FastAPIClient;
import com.hcsy.spring.common.client.GinClient;
import com.hcsy.spring.common.client.NestjsClient;
import com.hcsy.spring.entity.po.Result;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api_spring")
@RequiredArgsConstructor
@Slf4j
@Tag(name = "测试模块", description = "测试相关接口")
public class TestController {
    private final GinClient ginClient;
    private final NestjsClient nestjsClient;
    private final FastAPIClient fastAPIClient;

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
}

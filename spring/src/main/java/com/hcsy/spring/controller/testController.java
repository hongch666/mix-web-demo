package com.hcsy.spring.controller;

import com.hcsy.spring.client.GinClient;
import com.hcsy.spring.client.NestjsClient;
import com.hcsy.spring.po.Result;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api_spring")
@RequiredArgsConstructor
@Tag(name = "测试模块", description = "测试相关接口")
public class testController {
    private final GinClient ginClient;
    private final NestjsClient nestjsClient;

    @GetMapping("/spring")
    @Operation(summary = "spring自己的测试", description = "输出欢迎信息")
    public Result getHello() {
        return Result.success("Hello,I am Spring!");
    }

    @GetMapping("/gin")
    @Operation(summary = "调用Gin的测试", description = "输出欢迎信息")
    public Result gerGin() {
        return ginClient.testGin();
    }

    @GetMapping("/nestjs")
    @Operation(summary = "调用NestJS的测试", description = "输出欢迎信息")
    public Result gerNestjs() {
        return nestjsClient.testNestjs();
    }
}

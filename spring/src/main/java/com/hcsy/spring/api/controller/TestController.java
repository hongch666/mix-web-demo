package com.hcsy.spring.api.controller;

import com.hcsy.spring.common.client.FastAPIClient;
import com.hcsy.spring.common.client.GinClient;
import com.hcsy.spring.common.client.NestjsClient;
import com.hcsy.spring.common.utils.SimpleLogger;
import com.hcsy.spring.common.utils.UserContext;
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
    private final SimpleLogger logger;

    @GetMapping("/spring")
    @Operation(summary = "spring自己的测试", description = "输出欢迎信息")
    public Result getHello() {
        Long userId = UserContext.getUserId();
        String userName = UserContext.getUsername();
        // log.info("用户" + userId + ":" + userName + " GET /api_spring/sprng: " +
        // "测试Spring服务");
        logger.info("用户" + userId + ":" + userName + " GET /api_spring/spring: " + "测试Spring服务");
        return Result.success("Hello,I am Spring!");
    }

    @GetMapping("/gin")
    @Operation(summary = "调用Gin的测试", description = "输出欢迎信息")
    public Result gerGin() {
        Long userId = UserContext.getUserId();
        String userName = UserContext.getUsername();
        logger.info("用户" + userId + ":" + userName + " GET /api_spring/gin: " + "测试Gin服务");
        return ginClient.testGin();
    }

    @GetMapping("/nestjs")
    @Operation(summary = "调用NestJS的测试", description = "输出欢迎信息")
    public Result gerNestjs() {
        Long userId = UserContext.getUserId();
        String userName = UserContext.getUsername();
        logger.info("用户" + userId + ":" + userName + " GET /api_spring/nestjs: " + "测试NestJS服务");
        return nestjsClient.testNestjs();
    }

    @GetMapping("/fastapi")
    @Operation(summary = "调用FastAPI的测试", description = "输出欢迎信息")
    public Result gerFastAPI() {
        Long userId = UserContext.getUserId();
        String userName = UserContext.getUsername();
        logger.info("用户" + userId + ":" + userName + " GET /api_spring/fastapi: " + "测试FastAPI服务");
        return fastAPIClient.testFastAPI();
    }
}

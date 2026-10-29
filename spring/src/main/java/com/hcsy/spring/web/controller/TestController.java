package com.hcsy.spring.web.controller;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.hcsy.spring.common.constants.Defaults;
import com.hcsy.spring.common.utils.Result;
import com.hcsy.spring.web.logging.annotation.ApiLog;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import reactor.core.publisher.Mono;

/**
 * 测试控制器，提供 /test/spring 健康检查接口用于验证 Spring 服务是否正常运行
 */
@RestController
@RequestMapping("/test")
@RequiredArgsConstructor
@Tag(name = "测试模块", description = "服务测试相关API，用于验证各个微服务是否正常运行")
public class TestController {

    /**
     * GET /test/spring 接口，返回固定的欢迎信息，用于验证Spring服务是否正常运行
     */
    @GetMapping("/spring")
    @Operation(summary = "测试Spring服务", description = "输出欢迎信息")
    @ApiLog("测试Spring服务")
    public Mono<Result<String>> getHello() {
        return Mono.just(Result.success(Defaults.TEST));
    }
}

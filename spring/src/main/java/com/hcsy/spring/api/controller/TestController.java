package com.hcsy.spring.api.controller;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.hcsy.spring.common.constants.Defaults;
import com.hcsy.spring.common.utils.Result;
import com.hcsy.spring.core.annotation.ApiLog;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;

@RestController
@RequestMapping("/test")
@RequiredArgsConstructor
@Tag(name = "测试模块", description = "服务测试相关API，用于验证各个微服务是否正常运行")
public class TestController {

    @GetMapping("/spring")
    @Operation(summary = "Spring自己的测试", description = "输出欢迎信息")
    @ApiLog("测试Spring服务")
    public Result<String> getHello() {
        return Result.success(Defaults.TEST);
    }
}

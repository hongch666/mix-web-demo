package com.hcsy.spring.web.controller;

import java.util.List;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.hcsy.spring.application.service.OssReferenceService;
import com.hcsy.spring.common.utils.Result;
import com.hcsy.spring.web.logging.annotation.ApiLog;
import com.hcsy.spring.web.security.annotation.RequireInternalToken;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import reactor.core.publisher.Mono;

/**
 * OSS 在用引用查询接口，供 NestJS 定时清理任务通过内部令牌调用
 * 路径归属 OSS 域（/oss），不再挂在用户模块 /users 下
 */
@RestController
@RequestMapping("/oss")
@RequiredArgsConstructor
@Tag(name = "OSS对象模块", description = "OSS 对象在用引用查询相关API，供清理任务判断在用对象")
public class OssReferenceController {
    private final OssReferenceService ossReferenceService;

    /**
     * 查询 Spring 库中在用的 OSS 对象 key（用户头像与分类权威参考文本）
     */
    @GetMapping("/internal/references")
    @Operation(summary = "查询 OSS 在用引用 key", description = "返回数据库中在用的 OSS 对象 key 列表，供清理任务排除")
    @RequireInternalToken
    @ApiLog(value = "查询 OSS 在用引用 key", skipMq = true)
    public Mono<Result<List<String>>> listOssReferenceUrls() {
        return ossReferenceService.listOssReferenceUrls().map(Result::success);
    }
}

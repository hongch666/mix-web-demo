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
import lombok.RequiredArgsConstructor;
import reactor.core.publisher.Mono;

/**
 * OSS 在用引用查询接口，供 NestJS 定时清理任务通过内部令牌调用
 */
@RestController
@RequestMapping("/users")
@RequiredArgsConstructor
public class OssReferenceController {
    private final OssReferenceService ossReferenceService;

    /**
     * 查询 Spring 库中在用的 OSS 对象 key（用户头像与分类权威参考文本）
     */
    @GetMapping("/internal/oss-references")
    @Operation(summary = "查询 OSS 在用引用 key", description = "返回数据库中在用的 OSS 对象 key 列表，供清理任务排除")
    @RequireInternalToken
    @ApiLog("查询 OSS 在用引用 key")
    public Mono<Result<List<String>>> listOssReferenceUrls() {
        return ossReferenceService.listOssReferenceUrls().map(Result::success);
    }
}

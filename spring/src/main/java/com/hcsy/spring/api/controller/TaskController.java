package com.hcsy.spring.api.controller;

import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.hcsy.spring.common.utils.Result;
import com.hcsy.spring.core.annotation.ApiLog;
import com.hcsy.spring.core.annotation.RequireInternalToken;
import com.hcsy.spring.infra.task.TokenCleanupTask;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;

@RestController
@RequestMapping("/task")
@RequiredArgsConstructor
@Tag(name = "定时任务模块", description = "手动触发定时任务相关API")
public class TaskController {
    private final TokenCleanupTask tokenCleanupTask;

    @PostMapping("/clean")
    @Operation(summary = "手动执行清理过期Token", description = "手动触发清理过期Token任务")
    @RequireInternalToken
    @ApiLog("手动执行清理过期Token任务")
    public Result<Void> executeTokenCleanup() {
        tokenCleanupTask.cleanupExpiredTokens();
        return Result.success();
    }
}

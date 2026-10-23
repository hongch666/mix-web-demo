package com.hcsy.spring.web.controller;

import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.hcsy.spring.application.service.TaskService;
import com.hcsy.spring.common.utils.Result;
import com.hcsy.spring.web.logging.annotation.ApiLog;
import com.hcsy.spring.web.security.annotation.RequireInternalToken;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import reactor.core.publisher.Mono;

/**
 * 定时任务控制器，提供 /task/clean 内部接口用于手动触发过期Token清理任务
 */
@RestController
@RequestMapping("/task")
@RequiredArgsConstructor
@Tag(name = "定时任务模块", description = "手动触发定时任务相关API")
public class TaskController {
    private final TaskService taskService;

    /**
     * POST /task/clean 内部接口，手动触发清理过期Token任务并立即返回成功
     */
    @PostMapping("/clean")
    @Operation(summary = "手动执行清理过期Token", description = "手动触发清理过期Token任务")
    @RequireInternalToken
    @ApiLog("手动执行清理过期Token任务")
    public Mono<Result<Void>> executeTokenCleanup() {
        return taskService.triggerTokenCleanup().thenReturn(Result.success());
    }
}

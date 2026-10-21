package com.hcsy.spring.web.controller;

import java.time.LocalDateTime;

import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import com.hcsy.spring.application.service.WarehouseSyncService;
import com.hcsy.spring.application.service.WarehouseSyncService.SyncPage;
import com.hcsy.spring.common.utils.Result;
import com.hcsy.spring.web.security.annotation.RequireInternalToken;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import reactor.core.publisher.Mono;

/**
 * 数仓同步控制器，提供 /warehouse/sync/{resource} 内部接口供 FastAPI 数仓任务增量分页同步业务数据
 */
@RestController
@RequestMapping("/warehouse")
@RequiredArgsConstructor
@Tag(name = "数仓同步模块")
public class WarehouseSyncController {

    private final WarehouseSyncService warehouseSyncService;

    /**
     * GET /warehouse/sync/{resource} 内部接口，按资源名与更新时间增量分页返回业务表数据，供 FastAPI 数仓任务同步
     */
    @GetMapping("/sync/{resource}")
    @RequireInternalToken
    @Operation(summary = "分页获取数仓源数据", description = "供 FastAPI 数仓任务通过内部接口分页同步 Spring 业务数据")
    public Mono<Result<SyncPage>> sync(
        @PathVariable String resource,
        @RequestParam(defaultValue = "1970-01-01 00:00:00") @DateTimeFormat(
            pattern = "yyyy-MM-dd HH:mm:ss") LocalDateTime updatedAfter,
        @RequestParam(defaultValue = "1") int page,
        @RequestParam(defaultValue = "1000") int size) {
        return warehouseSyncService.sync(resource, updatedAfter, page, size)
            .map(Result::success);
    }
}

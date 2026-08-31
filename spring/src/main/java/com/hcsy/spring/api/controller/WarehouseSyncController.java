package com.hcsy.spring.api.controller;

import java.time.LocalDateTime;

import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import com.hcsy.spring.api.service.WarehouseSyncService;
import com.hcsy.spring.api.service.WarehouseSyncService.SyncPage;
import com.hcsy.spring.common.constants.Messages;
import com.hcsy.spring.common.utils.Result;
import com.hcsy.spring.core.annotation.RequireInternalToken;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import reactor.core.publisher.Mono;

@RestController
@RequestMapping("/warehouse")
@RequiredArgsConstructor
@Tag(name = Messages.WAREHOUSE_SYNC_TAG)
public class WarehouseSyncController {

    private final WarehouseSyncService warehouseSyncService;

    @GetMapping("/sync/{resource}")
    @RequireInternalToken
    @Operation(summary = Messages.WAREHOUSE_SYNC_SUMMARY, description = Messages.WAREHOUSE_SYNC_DESCRIPTION)
    public Mono<Result<SyncPage>> sync(
        @PathVariable String resource,
        @RequestParam(defaultValue = "1970-01-01 00:00:00")
        @DateTimeFormat(pattern = "yyyy-MM-dd HH:mm:ss") LocalDateTime updatedAfter,
        @RequestParam(defaultValue = "1") int page,
        @RequestParam(defaultValue = "1000") int size) {
        return warehouseSyncService.sync(resource, updatedAfter, page, size)
            .map(Result::success);
    }
}

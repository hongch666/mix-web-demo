package com.hcsy.spring.application.service;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

import reactor.core.publisher.Mono;

/**
 * 数仓同步业务接口，定义按资源类型与增量时间分页同步业务数据并返回同步分页结果的响应式操作
 */
public interface WarehouseSyncService {

    /**
     * 按资源类型与增量时间分页同步数据，基于水位线返回数据页的Mono响应式结果
     */
    Mono<SyncPage> sync(String resource, LocalDateTime updatedAfter, int page, int size);

    /**
     * 仓库同步的分页结果，包含数据行、页码、页大小、是否还有更多及上界水位时间
     */
    record SyncPage(
        List<Map<String, Object>> list,
        int page,
        int size,
        boolean hasMore,
        LocalDateTime upperWatermark) {
    }
}

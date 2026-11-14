package com.hcsy.spring.application.service;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

import io.swagger.v3.oas.annotations.media.Schema;
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
    @Schema(description = "数仓同步的分页结果，按增量水位线分页返回")
    record SyncPage(
        @Schema(description = "当前页的数据行，每行为一张表的字段到取值的映射") List<Map<String, Object>> list,
        @Schema(description = "当前页码，从 1 开始") int page,
        @Schema(description = "每页条数") int size,
        @Schema(description = "是否还有下一页，可据此继续翻页") boolean hasMore,
        @Schema(description = "本次返回数据的上界水位时间，下次增量同步以它为 updatedAfter") LocalDateTime upperWatermark) {
    }
}

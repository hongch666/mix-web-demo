package com.hcsy.spring.api.service;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

import reactor.core.publisher.Mono;

public interface WarehouseSyncService {

    Mono<SyncPage> sync(String resource, LocalDateTime updatedAfter, int page, int size);

    record SyncPage(
        List<Map<String, Object>> list,
        int page,
        int size,
        boolean hasMore,
        LocalDateTime upperWatermark) {
    }
}

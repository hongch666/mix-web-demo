package com.hcsy.spring.api.service.impl;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

import org.springframework.stereotype.Service;

import com.hcsy.spring.api.repository.WarehouseSyncRepository;
import com.hcsy.spring.api.service.WarehouseSyncService;
import com.hcsy.spring.common.constants.Messages;
import com.hcsy.spring.common.constants.WarehouseResources;
import com.hcsy.spring.common.constants.WarehouseResources.ResourceSpec;

import lombok.RequiredArgsConstructor;
import reactor.core.publisher.Mono;

@Service
@RequiredArgsConstructor
public class WarehouseSyncServiceImpl implements WarehouseSyncService {

    private final WarehouseSyncRepository warehouseSyncRepository;

    @Override
    public Mono<SyncPage> sync(String resource, LocalDateTime updatedAfter, int page, int size) {
        ResourceSpec spec = WarehouseResources.ALL.get(resource);
        if (spec == null) {
            return Mono.error(new IllegalArgumentException(
                String.format(Messages.WAREHOUSE_UNSUPPORTED_RESOURCE, resource)));
        }

        int safePage = Math.max(page, 1);
        int safeSize = Math.min(Math.max(size, 1), 5000);
        int offset = (safePage - 1) * safeSize;
        return warehouseSyncRepository.findLatest(spec.entityType(), spec.watermarkProperty())
            .map(spec.watermarkGetter())
            .flatMap(upperBound -> warehouseSyncRepository
                .findUpdated(spec.entityType(), spec.watermarkProperty(), updatedAfter, upperBound,
                    offset, safeSize + 1)
                .map(spec.rowMapper())
                .collectList()
                .map(rows -> toPage(rows, safePage, safeSize, upperBound)))
            .defaultIfEmpty(new SyncPage(List.of(), safePage, safeSize, false, updatedAfter));
    }

    private SyncPage toPage(
        List<Map<String, Object>> rows,
        int page,
        int size,
        LocalDateTime upperWatermark) {
        boolean hasMore = rows.size() > size;
        List<Map<String, Object>> result = hasMore ? rows.subList(0, size) : rows;
        return new SyncPage(result, page, size, hasMore, upperWatermark);
    }
}

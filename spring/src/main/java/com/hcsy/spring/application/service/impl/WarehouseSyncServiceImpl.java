package com.hcsy.spring.application.service.impl;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

import org.springframework.data.domain.Sort;
import org.springframework.data.r2dbc.core.R2dbcEntityTemplate;
import org.springframework.data.relational.core.query.Criteria;
import org.springframework.data.relational.core.query.Query;
import org.springframework.stereotype.Service;
import org.springframework.util.ReflectionUtils;

import com.hcsy.spring.application.service.WarehouseSyncService;
import com.hcsy.spring.common.constants.Messages;
import com.hcsy.spring.common.constants.WarehouseResources;
import com.hcsy.spring.common.constants.WarehouseResources.ResourceSpec;

import jakarta.annotation.PostConstruct;
import lombok.RequiredArgsConstructor;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

/**
 * WarehouseSyncService 的实现，按资源规格解析水位线并对业务表增量数据分页查询，自动修正分页参数后封装为同步分页结果
 */
@Service
@RequiredArgsConstructor
public class WarehouseSyncServiceImpl implements WarehouseSyncService {

    private final R2dbcEntityTemplate entityTemplate;

    /**
     * 启动期校验资源规格：水位线属性写错时直接启动失败，而不是等到第一次同步才抛 SQL 错误
     */
    @PostConstruct
    void validateResourceSpecs() {
        WarehouseResources.ALL.forEach((resource, spec) -> {
            if (spec.watermarkProperty() == null || spec.watermarkProperty().isBlank()
                || spec.watermarkGetter() == null || spec.rowMapper() == null) {
                throw new IllegalStateException(String.format(Messages.WAREHOUSE_SPEC_INCOMPLETE, resource));
            }
            if (ReflectionUtils.findField(spec.entityType(), spec.watermarkProperty()) == null) {
                throw new IllegalStateException(String.format(Messages.WAREHOUSE_SPEC_INVALID_PROPERTY, resource,
                    spec.watermarkProperty(), spec.entityType().getSimpleName()));
            }
        });
    }

    /**
     * 按资源规格解析数据水位线并分页查询增量数据，自动修正分页参数后封装为同步分页结果返回
     */
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
        return findLatest(spec.entityType(), spec.watermarkProperty())
            .map(spec.watermarkGetter())
            .flatMap(upperBound -> findUpdated(spec.entityType(), spec.watermarkProperty(), updatedAfter,
                upperBound, offset, safeSize + 1)
                .map(spec.rowMapper())
                .collectList()
                .map(rows -> toPage(rows, safePage, safeSize, upperBound)))
            .defaultIfEmpty(new SyncPage(List.of(), safePage, safeSize, false, updatedAfter));
    }

    /**
     * 按水位线字段倒序查询最近的一条记录，用于取同步上界；水位线为 NULL 的行排在最后，不会成为上界
     */
    private <T> Mono<T> findLatest(Class<T> entityType, String watermarkProperty) {
        Query query = Query.empty()
            .sort(Sort.by(Sort.Order.desc(watermarkProperty), Sort.Order.desc("id")))
            .limit(1);
        return entityTemplate.select(query, entityType).next();
    }

    /**
     * 分页查询水位线字段落在指定区间内且按水位线升序排列的实体，用于数仓增量同步抓取
     *
     * updatedAfter 为空表示全量同步（取上界以内的全部数据）；水位线为 NULL 的行在 SQL 里不满足
     * 「大于」比较，只按区间过滤会永远同步不到，因此额外放行 NULL：这类行每次同步都会被带出
     * （不受上界约束），但不会漏数据；表上水位线字段都有默认值，正常情况下集合为空
     */
    private <T> Flux<T> findUpdated(
        Class<T> entityType,
        String watermarkProperty,
        LocalDateTime updatedAfter,
        LocalDateTime upperBound,
        int offset,
        int limit) {
        Criteria ranged = Criteria.where(watermarkProperty).lessThanOrEquals(upperBound);
        if (updatedAfter != null) {
            ranged = Criteria.where(watermarkProperty)
                .greaterThan(updatedAfter)
                .and(Criteria.where(watermarkProperty).lessThanOrEquals(upperBound));
        }
        Criteria criteria = ranged.or(Criteria.where(watermarkProperty).isNull());
        Query query = Query.query(criteria)
            .sort(Sort.by(Sort.Order.asc(watermarkProperty), Sort.Order.asc("id")))
            .limit(limit)
            .offset(offset);
        return entityTemplate.select(query, entityType);
    }

    /**
     * 将查询结果裁剪至页大小并计算是否还有更多数据，组装为同步分页对象
     */
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

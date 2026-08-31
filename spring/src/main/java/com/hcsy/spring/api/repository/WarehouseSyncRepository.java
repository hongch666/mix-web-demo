package com.hcsy.spring.api.repository;

import java.time.LocalDateTime;

import org.springframework.data.domain.Sort;
import org.springframework.data.r2dbc.core.R2dbcEntityTemplate;
import org.springframework.data.relational.core.query.Criteria;
import org.springframework.data.relational.core.query.Query;
import org.springframework.stereotype.Repository;

import lombok.RequiredArgsConstructor;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

/**
 * 数仓同步数据访问层，使用 Spring Data R2DBC 实体查询
 */
@Repository
@RequiredArgsConstructor
public class WarehouseSyncRepository {

    private final R2dbcEntityTemplate entityTemplate;

    public <T> Mono<T> findLatest(Class<T> entityType, String watermarkProperty) {
        Query query = Query.empty()
            .sort(Sort.by(Sort.Order.desc(watermarkProperty), Sort.Order.desc("id")))
            .limit(1);
        return entityTemplate.select(query, entityType).next();
    }

    public <T> Flux<T> findUpdated(
        Class<T> entityType,
        String watermarkProperty,
        LocalDateTime updatedAfter,
        LocalDateTime upperBound,
        int offset,
        int limit) {
        Criteria criteria = Criteria.where(watermarkProperty)
            .greaterThan(updatedAfter)
            .and(watermarkProperty)
            .lessThanOrEquals(upperBound);
        Query query = Query.query(criteria)
            .sort(Sort.by(Sort.Order.asc(watermarkProperty), Sort.Order.asc("id")))
            .limit(limit)
            .offset(offset);
        return entityTemplate.select(query, entityType);
    }
}

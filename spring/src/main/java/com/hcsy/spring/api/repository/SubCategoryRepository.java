package com.hcsy.spring.api.repository;

import java.time.LocalDateTime;

import org.springframework.data.r2dbc.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.data.repository.reactive.ReactiveCrudRepository;

import com.hcsy.spring.entity.po.SubCategory;

import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

public interface SubCategoryRepository extends ReactiveCrudRepository<SubCategory, Long> {
    Flux<SubCategory> findByCategoryIdOrderByIdAsc(Long categoryId);

    Mono<Void> deleteByCategoryId(Long categoryId);

    /**
     * 查询 update_time > :after 的子分类，用于Neo4j增量同步
     */
    @Query("SELECT * FROM sub_category WHERE update_time > :after")
    Flux<SubCategory> findByUpdateTimeAfter(@Param("after") LocalDateTime after);
}

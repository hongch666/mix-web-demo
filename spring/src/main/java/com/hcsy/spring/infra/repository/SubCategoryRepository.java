package com.hcsy.spring.infra.repository;

import java.time.LocalDateTime;

import org.springframework.data.r2dbc.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.data.repository.reactive.ReactiveCrudRepository;

import com.hcsy.spring.entity.po.SubCategory;

import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

/**
 * 负责子分类实体（SubCategory）的响应式数据访问，含分类下子分类查询与 Neo4j 增量同步
 */
public interface SubCategoryRepository extends ReactiveCrudRepository<SubCategory, Long> {
    /**
     * 按 ID 升序查询指定分类下的全部子分类
     */
    Flux<SubCategory> findByCategoryIdOrderByIdAsc(Long categoryId);

    /**
     * 删除指定分类下的全部子分类
     */
    Mono<Void> deleteByCategoryId(Long categoryId);

    /**
     * 查询 update_time > :after 的子分类，用于Neo4j增量同步
     */
    @Query("SELECT * FROM sub_category WHERE update_time > :after")
    Flux<SubCategory> findByUpdateTimeAfter(@Param("after") LocalDateTime after);
}

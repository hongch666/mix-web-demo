package com.hcsy.spring.infra.repository;

import java.time.LocalDateTime;

import org.springframework.data.domain.Pageable;
import org.springframework.data.r2dbc.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.data.repository.reactive.ReactiveCrudRepository;

import com.hcsy.spring.entity.po.Category;

import reactor.core.publisher.Flux;

/**
 * 负责文章分类实体（Category）的响应式数据访问，含分页列表与 Neo4j 增量同步查询
 */
public interface CategoryRepository extends ReactiveCrudRepository<Category, Long> {
    /**
     * 按 ID 升序分页查询全部分类列表
     */
    Flux<Category> findAllByOrderByIdAsc(Pageable pageable);

    /**
     * 查询 update_time > :after 的分类，用于Neo4j增量同步
     */
    @Query("SELECT * FROM category WHERE update_time > :after")
    Flux<Category> findByUpdateTimeAfter(@Param("after") LocalDateTime after);
}

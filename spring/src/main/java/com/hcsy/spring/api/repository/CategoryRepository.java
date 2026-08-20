package com.hcsy.spring.api.repository;

import java.time.LocalDateTime;

import org.springframework.data.domain.Pageable;
import org.springframework.data.r2dbc.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.data.repository.reactive.ReactiveCrudRepository;

import com.hcsy.spring.entity.po.Category;

import reactor.core.publisher.Flux;

public interface CategoryRepository extends ReactiveCrudRepository<Category, Long> {
    Flux<Category> findAllByOrderByIdAsc(Pageable pageable);

    /**
     * 查询 update_time > :after 的分类，用于Neo4j增量同步
     */
    @Query("SELECT * FROM category WHERE update_time > :after")
    Flux<Category> findByUpdateTimeAfter(@Param("after") LocalDateTime after);
}

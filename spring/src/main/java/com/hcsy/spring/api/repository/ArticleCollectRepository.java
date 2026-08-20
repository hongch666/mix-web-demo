package com.hcsy.spring.api.repository;

import java.time.LocalDateTime;

import org.springframework.data.domain.Pageable;
import org.springframework.data.r2dbc.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.data.repository.reactive.ReactiveCrudRepository;

import com.hcsy.spring.entity.po.ArticleCollect;
import com.hcsy.spring.entity.projection.DateCountRow;

import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

public interface ArticleCollectRepository extends ReactiveCrudRepository<ArticleCollect, Long> {
    Mono<Boolean> existsByArticleIdAndUserId(Long articleId, Long userId);

    Mono<Void> deleteByArticleIdAndUserId(Long articleId, Long userId);

    Flux<ArticleCollect> findByUserIdOrderByCreatedTimeDesc(Long userId, Pageable pageable);

    Mono<Long> countByUserId(Long userId);

    Mono<Long> countByArticleId(Long articleId);

    @Query("""
        SELECT DATE(created_time) AS date, COUNT(*) AS count
        FROM collects
        WHERE user_id = :userId AND created_time >= :firstDay AND created_time < :lastDay
        GROUP BY DATE(created_time)
        ORDER BY DATE(created_time)
        """)
    Flux<DateCountRow> countMonthlyByUserIdGroupByDate(
        @Param("userId") Long userId,
        @Param("firstDay") LocalDateTime firstDay,
        @Param("lastDay") LocalDateTime lastDay);
}

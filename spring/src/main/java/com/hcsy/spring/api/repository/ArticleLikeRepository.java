package com.hcsy.spring.api.repository;

import java.time.LocalDateTime;

import org.springframework.data.domain.Pageable;
import org.springframework.data.r2dbc.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.data.repository.reactive.ReactiveCrudRepository;

import com.hcsy.spring.entity.po.ArticleLike;
import com.hcsy.spring.entity.projection.DateCountRow;

import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

public interface ArticleLikeRepository extends ReactiveCrudRepository<ArticleLike, Long> {
    Mono<Boolean> existsByArticleIdAndUserId(Long articleId, Long userId);

    Mono<Void> deleteByArticleIdAndUserId(Long articleId, Long userId);

    Flux<ArticleLike> findByUserIdOrderByCreatedTimeDesc(Long userId, Pageable pageable);

    Mono<Long> countByUserId(Long userId);

    Mono<Long> countByArticleId(Long articleId);

    @Query("""
        SELECT DATE(created_time) AS date, COUNT(*) AS count
        FROM likes
        WHERE user_id = :userId AND created_time >= :firstDay AND created_time < :lastDay
        GROUP BY DATE(created_time)
        ORDER BY DATE(created_time)
        """)
    Flux<DateCountRow> countMonthlyByUserIdGroupByDate(
        @Param("userId") Long userId,
        @Param("firstDay") LocalDateTime firstDay,
        @Param("lastDay") LocalDateTime lastDay);

    /**
     * 查询最近 :limit 条点赞记录（按 id 倒序），用于Neo4j同步全量抓取。
     * 点赞表数据量可达百万级，一次性全量加载会耗时过长并拖垮同步任务，
     * 故限制只取最近若干条。
     */
    @Query("SELECT * FROM likes ORDER BY id DESC LIMIT :limit")
    Flux<ArticleLike> findLatestForSync(@Param("limit") int limit);

    /**
     * 查询 created_time > :after 且不超过 :limit 条的点赞记录，用于Neo4j增量同步
     */
    @Query("SELECT * FROM likes WHERE created_time > :after ORDER BY id DESC LIMIT :limit")
    Flux<ArticleLike> findLatestAfterForSync(
        @Param("after") LocalDateTime after, @Param("limit") int limit);
}

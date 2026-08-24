package com.hcsy.spring.api.repository;

import java.time.LocalDateTime;
import java.util.Collection;

import org.springframework.data.domain.Pageable;
import org.springframework.data.r2dbc.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.data.repository.reactive.ReactiveCrudRepository;

import com.hcsy.spring.entity.po.ArticleCollect;
import com.hcsy.spring.entity.projection.DateCountRow;
import com.hcsy.spring.entity.projection.IdCountRow;

import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

public interface ArticleCollectRepository extends ReactiveCrudRepository<ArticleCollect, Long> {
    Mono<Boolean> existsByArticleIdAndUserId(Long articleId, Long userId);

    Mono<Void> deleteByArticleIdAndUserId(Long articleId, Long userId);

    Flux<ArticleCollect> findByUserIdOrderByCreatedTimeDesc(Long userId, Pageable pageable);

    Mono<Long> countByUserId(Long userId);

    Mono<Long> countByArticleId(Long articleId);

    /**
     * 批量统计多篇文章的收藏数，避免 N+1 查询
     */
    @Query("""
        SELECT article_id AS id, COUNT(*) AS count
        FROM collects
        WHERE article_id IN (:ids)
        GROUP BY article_id
        """)
    Flux<IdCountRow> countGroupByArticleIdIn(@Param("ids") Collection<Long> articleIds);

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

    /**
     * 查询最近 :limit 条收藏记录（按 id 倒序），用于Neo4j同步全量抓取。
     * 收藏表数据量可达百万级，一次性全量加载会耗时过长并拖垮同步任务。
     */
    @Query("SELECT * FROM collects ORDER BY id DESC LIMIT :limit")
    Flux<ArticleCollect> findLatestForSync(@Param("limit") int limit);

    /**
     * 查询 created_time > :after 且不超过 :limit 条的收藏记录，用于Neo4j增量同步
     */
    @Query("SELECT * FROM collects WHERE created_time > :after ORDER BY id DESC LIMIT :limit")
    Flux<ArticleCollect> findLatestAfterForSync(
        @Param("after") LocalDateTime after, @Param("limit") int limit);
}

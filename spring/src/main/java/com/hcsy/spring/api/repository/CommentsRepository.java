package com.hcsy.spring.api.repository;

import java.time.LocalDateTime;
import java.util.List;

import org.springframework.data.domain.Pageable;
import org.springframework.data.r2dbc.repository.Modifying;
import org.springframework.data.r2dbc.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.data.repository.reactive.ReactiveCrudRepository;

import com.hcsy.spring.entity.po.Comments;
import com.hcsy.spring.entity.projection.DateCountRow;

import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

public interface CommentsRepository extends ReactiveCrudRepository<Comments, Long> {
    Flux<Comments> findByUserIdOrderByCreateTimeDesc(Long userId, Pageable pageable);

    Mono<Long> countByUserId(Long userId);

    Flux<Comments> findByArticleIdOrderByCreateTimeDesc(Long articleId);

    Mono<Long> countByArticleIdAndUserIdIn(@Param("articleId") Long articleId, @Param("userIds") List<Long> userIds);

    @Modifying
    Mono<Integer> deleteByArticleIdAndUserIdIn(@Param("articleId") Long articleId, @Param("userIds") List<Long> userIds);

    @Query("""
        SELECT DATE(create_time) AS date, COUNT(*) AS count
        FROM comments
        WHERE user_id = :userId AND create_time >= :firstDay AND create_time < :lastDay
        GROUP BY DATE(create_time)
        ORDER BY DATE(create_time)
        """)
    Flux<DateCountRow> countMonthlyByUserIdGroupByDate(
        @Param("userId") Long userId,
        @Param("firstDay") LocalDateTime firstDay,
        @Param("lastDay") LocalDateTime lastDay);

    /**
     * 查询最近 :limit 条评论（按 id 倒序），用于Neo4j同步全量抓取。
     * 评论表数据量较大，一次性全量加载会耗时过长并拖垮同步任务。
     */
    @Query("SELECT * FROM comments ORDER BY id DESC LIMIT :limit")
    Flux<Comments> findLatestForSync(@Param("limit") int limit);

    /**
     * 查询 update_time > :after 且不超过 :limit 条的评论，用于Neo4j增量同步
     */
    @Query("SELECT * FROM comments WHERE update_time > :after ORDER BY id DESC LIMIT :limit")
    Flux<Comments> findLatestAfterForSync(
        @Param("after") LocalDateTime after, @Param("limit") int limit);
}

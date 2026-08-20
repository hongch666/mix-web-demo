package com.hcsy.spring.api.repository;

import java.time.LocalDateTime;

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

    @Query("""
        SELECT COUNT(*) FROM comments
        WHERE article_id = :articleId AND user_id IN (SELECT id FROM users WHERE role = 'ai')
        """)
    Mono<Long> countAiCommentsByArticleId(@Param("articleId") Long articleId);

    @Modifying
    @Query("""
        DELETE FROM comments
        WHERE article_id = :articleId AND user_id IN (SELECT id FROM users WHERE role = 'ai')
        """)
    Mono<Integer> deleteAiCommentsByArticleId(@Param("articleId") Long articleId);

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
     * 查询 update_time > :after 的评论，用于Neo4j增量同步
     */
    @Query("SELECT * FROM comments WHERE update_time > :after")
    Flux<Comments> findByUpdateTimeAfter(@Param("after") LocalDateTime after);
}

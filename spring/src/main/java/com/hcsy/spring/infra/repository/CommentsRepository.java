package com.hcsy.spring.infra.repository;

import java.time.LocalDateTime;
import java.util.List;

import org.springframework.data.domain.Pageable;
import org.springframework.data.r2dbc.repository.Modifying;
import org.springframework.data.r2dbc.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.data.repository.reactive.ReactiveCrudRepository;

import com.hcsy.spring.entity.po.Comments;
import com.hcsy.spring.entity.vo.DateCountVO;

import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

/**
 * 负责文章评论实体（Comments）的响应式数据访问，含评论查询、AI 评论清理与趋势统计
 */
public interface CommentsRepository extends ReactiveCrudRepository<Comments, Long> {
    /**
     * 按创建时间倒序分页查询指定用户发表的评论列表
     */
    Flux<Comments> findByUserIdOrderByCreateTimeDesc(Long userId, Pageable pageable);

    /**
     * 统计指定用户发表的评论总数
     */
    Mono<Long> countByUserId(Long userId);

    /**
     * 按创建时间倒序查询指定文章下的全部评论
     */
    Flux<Comments> findByArticleIdOrderByCreateTimeDesc(Long articleId);

    /**
     * 统计指定文章下来自给定用户集合的评论数量，用于统计 AI 用户评论数
     */
    Mono<Long> countByArticleIdAndUserIdIn(@Param("articleId") Long articleId, @Param("userIds") List<Long> userIds);

    /**
     * 删除指定文章下来自给定用户集合的评论，用于清理 AI 评论
     */
    @Modifying
    Mono<Integer> deleteByArticleIdAndUserIdIn(@Param("articleId") Long articleId,
        @Param("userIds") List<Long> userIds);

    /**
     * 按天分组统计用户在指定时间段内的评论数量并按日期升序返回，用于评论月度趋势统计
     */
    @Query("""
        SELECT DATE(create_time) AS date, COUNT(*) AS count
        FROM comments
        WHERE user_id = :userId AND create_time >= :firstDay AND create_time < :lastDay
        GROUP BY DATE(create_time)
        ORDER BY DATE(create_time)
        """)
    Flux<DateCountVO> countMonthlyByUserIdGroupByDate(
        @Param("userId") Long userId,
        @Param("firstDay") LocalDateTime firstDay,
        @Param("lastDay") LocalDateTime lastDay);

    /**
     * 查询最近 :limit 条评论（按 id 倒序），用于Neo4j同步全量抓取
     * 评论表数据量较大，一次性全量加载会耗时过长并拖垮同步任务
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

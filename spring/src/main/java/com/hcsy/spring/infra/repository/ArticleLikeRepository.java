package com.hcsy.spring.infra.repository;

import java.time.LocalDateTime;
import java.util.Collection;

import org.springframework.data.domain.Pageable;
import org.springframework.data.r2dbc.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.data.repository.reactive.ReactiveCrudRepository;

import com.hcsy.spring.entity.po.ArticleLike;
import com.hcsy.spring.entity.vo.DateCountVO;
import com.hcsy.spring.entity.vo.IdCountVO;

import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

/**
 * 负责文章点赞记录（ArticleLike）的响应式数据访问，含点赞判断、统计与同步抓取
 */
public interface ArticleLikeRepository extends ReactiveCrudRepository<ArticleLike, Long> {
    /**
     * 判断用户是否已点赞指定文章
     */
    Mono<Boolean> existsByArticleIdAndUserId(Long articleId, Long userId);

    /**
     * 删除用户对指定文章的点赞记录，用于取消点赞
     */
    Mono<Void> deleteByArticleIdAndUserId(Long articleId, Long userId);

    /**
     * 按点赞时间倒序分页查询用户点赞的文章记录
     */
    Flux<ArticleLike> findByUserIdOrderByCreatedTimeDesc(Long userId, Pageable pageable);

    /**
     * 统计用户点赞的文章总数
     */
    Mono<Long> countByUserId(Long userId);

    /**
     * 统计指定文章的点赞总数
     */
    Mono<Long> countByArticleId(Long articleId);

    /**
     * 批量统计多篇文章的点赞数，避免 N+1 查询
     */
    @Query("""
        SELECT article_id AS id, COUNT(*) AS count
        FROM likes
        WHERE article_id IN (:ids)
        GROUP BY article_id
        """)
    Flux<IdCountVO> countGroupByArticleIdIn(@Param("ids") Collection<Long> articleIds);

    /**
     * 按天分组统计用户在指定时间段内的点赞数量并按日期升序返回，用于点赞月度趋势统计
     */
    @Query("""
        SELECT DATE(created_time) AS date, COUNT(*) AS count
        FROM likes
        WHERE user_id = :userId AND created_time >= :firstDay AND created_time < :lastDay
        GROUP BY DATE(created_time)
        ORDER BY DATE(created_time)
        """)
    Flux<DateCountVO> countMonthlyByUserIdGroupByDate(
        @Param("userId") Long userId,
        @Param("firstDay") LocalDateTime firstDay,
        @Param("lastDay") LocalDateTime lastDay);

    /**
     * 查询最近 :limit 条点赞记录（按 id 倒序），用于Neo4j同步全量抓取
     * 点赞表数据量可达百万级，一次性全量加载会耗时过长并拖垮同步任务，故限制只取最近若干条
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

package com.hcsy.spring.api.repository;

import java.time.LocalDateTime;
import java.util.Collection;
import java.util.Map;

import org.springframework.data.domain.Pageable;
import org.springframework.data.r2dbc.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.data.repository.reactive.ReactiveCrudRepository;

import com.hcsy.spring.entity.po.Focus;
import com.hcsy.spring.entity.projection.DateCountRow;

import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

public interface FocusRepository extends ReactiveCrudRepository<Focus, Long> {
    Mono<Boolean> existsByUserIdAndFocusId(Long userId, Long focusId);

    Mono<Void> deleteByUserIdAndFocusId(Long userId, Long focusId);

    Flux<Focus> findByUserIdOrderByCreatedTimeDesc(Long userId, Pageable pageable);

    Flux<Focus> findByFocusIdOrderByCreatedTimeDesc(Long focusId, Pageable pageable);

    Mono<Long> countByUserId(Long userId);

    Mono<Long> countByFocusId(Long focusId);

    /**
     * 批量统计多个用户的被关注数，避免 N+1 查询
     */
    @Query("""
        SELECT focus_id, COUNT(*) AS cnt
        FROM focus
        WHERE focus_id IN (:ids)
        GROUP BY focus_id
        """)
    Flux<Map<String, Object>> countGroupByFocusIdIn(@Param("ids") Collection<Long> userIds);

    @Query("""
        SELECT COUNT(*) FROM focus
        WHERE focus_id = :userId AND created_time >= :startDate AND created_time <= :endDate
        """)
    Mono<Long> countFollowersInPeriod(
        @Param("userId") Long userId,
        @Param("startDate") LocalDateTime startDate,
        @Param("endDate") LocalDateTime endDate);

    @Query("""
        SELECT DATE(created_time) AS date, COUNT(*) AS count
        FROM focus
        WHERE user_id = :userId AND created_time >= :startDate AND created_time <= :endDate
        GROUP BY DATE(created_time)
        ORDER BY DATE(created_time)
        """)
    Flux<DateCountRow> countDailyFollowsByUserIdAndPeriod(
        @Param("userId") Long userId,
        @Param("startDate") LocalDateTime startDate,
        @Param("endDate") LocalDateTime endDate);

    @Query("SELECT COUNT(*) FROM focus WHERE user_id = :userId")
    Mono<Long> countTotalFollowsByUserId(@Param("userId") Long userId);

    @Query("""
        SELECT DATE(created_time) AS date, COUNT(*) AS count
        FROM focus
        WHERE user_id = :userId AND created_time >= :firstDay AND created_time < :lastDay
        GROUP BY DATE(created_time)
        ORDER BY DATE(created_time)
        """)
    Flux<DateCountRow> countMonthlyByUserIdGroupByDate(
        @Param("userId") Long userId,
        @Param("firstDay") LocalDateTime firstDay,
        @Param("lastDay") LocalDateTime lastDay);

    /**
     * 查询最近 :limit 条关注记录（按 id 倒序），用于Neo4j同步全量抓取。
     * 关注表数据量较大，一次性全量加载会耗时过长并拖垮同步任务。
     */
    @Query("SELECT * FROM focus ORDER BY id DESC LIMIT :limit")
    Flux<Focus> findLatestForSync(@Param("limit") int limit);

    /**
     * 查询 created_time > :after 且不超过 :limit 条的关注记录，用于Neo4j增量同步
     */
    @Query("SELECT * FROM focus WHERE created_time > :after ORDER BY id DESC LIMIT :limit")
    Flux<Focus> findLatestAfterForSync(
        @Param("after") LocalDateTime after, @Param("limit") int limit);
}

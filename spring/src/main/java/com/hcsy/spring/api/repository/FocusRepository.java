package com.hcsy.spring.api.repository;

import java.time.LocalDateTime;

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
}

package com.hcsy.spring.infra.repository;

import java.time.LocalDateTime;
import java.util.Collection;

import org.springframework.data.domain.Pageable;
import org.springframework.data.r2dbc.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.data.repository.reactive.ReactiveCrudRepository;

import com.hcsy.spring.entity.po.Focus;
import com.hcsy.spring.entity.vo.DateCountVO;
import com.hcsy.spring.entity.vo.IdCountVO;

import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

/**
 * 负责用户关注关系实体（Focus）的响应式数据访问，含关注与粉丝的查询统计及同步抓取
 */
public interface FocusRepository extends ReactiveCrudRepository<Focus, Long> {
    /**
     * 判断用户是否已关注指定用户
     */
    Mono<Boolean> existsByUserIdAndFocusId(Long userId, Long focusId);

    /**
     * 删除用户对指定用户的关注记录，用于取消关注
     */
    Mono<Void> deleteByUserIdAndFocusId(Long userId, Long focusId);

    /**
     * 按关注时间倒序分页查询用户关注的人列表
     */
    Flux<Focus> findByUserIdOrderByCreatedTimeDesc(Long userId, Pageable pageable);

    /**
     * 按关注时间倒序分页查询关注指定用户的粉丝列表
     */
    Flux<Focus> findByFocusIdOrderByCreatedTimeDesc(Long focusId, Pageable pageable);

    /**
     * 统计用户关注他人的数量
     */
    Mono<Long> countByUserId(Long userId);

    /**
     * 统计指定用户的被关注（粉丝）数量
     */
    Mono<Long> countByFocusId(Long focusId);

    /**
     * 批量统计多个用户的被关注数，避免 N+1 查询
     */
    @Query("""
        SELECT focus_id AS id, COUNT(*) AS count
        FROM focus
        WHERE focus_id IN (:ids)
        GROUP BY focus_id
        """)
    Flux<IdCountVO> countGroupByFocusIdIn(@Param("ids") Collection<Long> userIds);

    /**
     * 统计指定用户在时间段内新增的粉丝数量
     */
    @Query("""
        SELECT COUNT(*) FROM focus
        WHERE focus_id = :userId AND created_time >= :startDate AND created_time <= :endDate
        """)
    Mono<Long> countFollowersInPeriod(
        @Param("userId") Long userId,
        @Param("startDate") LocalDateTime startDate,
        @Param("endDate") LocalDateTime endDate);

    /**
     * 按天分组统计用户在时间段内关注他人的数量并按日期升序返回
     */
    @Query("""
        SELECT DATE(created_time) AS date, COUNT(*) AS count
        FROM focus
        WHERE user_id = :userId AND created_time >= :startDate AND created_time <= :endDate
        GROUP BY DATE(created_time)
        ORDER BY DATE(created_time)
        """)
    Flux<DateCountVO> countDailyFollowsByUserIdAndPeriod(
        @Param("userId") Long userId,
        @Param("startDate") LocalDateTime startDate,
        @Param("endDate") LocalDateTime endDate);

    /**
     * 统计用户累计关注他人的总数
     */
    @Query("SELECT COUNT(*) FROM focus WHERE user_id = :userId")
    Mono<Long> countTotalFollowsByUserId(@Param("userId") Long userId);

    /**
     * 查询最近 :limit 条关注记录（按 id 倒序），用于Neo4j同步全量抓取
     * 关注表数据量较大，一次性全量加载会耗时过长并拖垮同步任务
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

package com.hcsy.spring.api.service;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

import com.hcsy.spring.entity.dto.PageDTO;
import com.hcsy.spring.entity.vo.FocusUserVO;

import reactor.core.publisher.Mono;

public interface FocusService {
    Mono<Boolean> addFocus(Long userId, Long focusId);

    Mono<Boolean> removeFocus(Long userId, Long focusId);

    Mono<Boolean> isFocused(Long userId, Long focusId);

    Mono<PageDTO<FocusUserVO>> listUserFocuses(Long userId, long page, long size);

    Mono<PageDTO<FocusUserVO>> listUserFollowers(Long userId, long page, long size);

    Mono<Long> getFocusCountByUserId(Long userId);

    Mono<Long> getFollowerCountByUserId(Long userId);

    Mono<Map<Long, Long>> getFollowCountsByUserIds(java.util.Collection<Long> userIds);

    /**
     * 获取指定时间段内的新增粉丝数
     */
    Mono<Long> getFollowersInPeriod(Long userId, LocalDateTime startDate, LocalDateTime endDate);

    /**
     * 获取指定时间段内每天的关注数
     */
    Mono<Map<String, Object>> getDailyFollows(Long userId, LocalDateTime startDate, LocalDateTime endDate);

    /**
     * 获取用户的总关注数
     */
    Mono<Long> getTotalFollows(Long userId);

    /**
     * 获取用户本月关注的趋势
     */
    Mono<Map<String, Object>> getMonthlyFollowTrend(Long userId);

    /**
     * 获取关注数据，用于Neo4j同步
     *
     * @param updatedAfter
     *                         增量同步时间（ISO格式），为空则全量
     */
    Mono<List<Map<String, Object>>> getNeo4jSyncFocus(String updatedAfter);
}

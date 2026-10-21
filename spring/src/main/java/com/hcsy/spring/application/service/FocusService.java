package com.hcsy.spring.application.service;

import java.time.LocalDateTime;
import java.util.List;

import com.hcsy.spring.entity.dto.PageDTO;
import com.hcsy.spring.entity.vo.BatchCountVO;
import com.hcsy.spring.entity.vo.FocusSyncVO;
import com.hcsy.spring.entity.vo.FocusUserVO;
import com.hcsy.spring.entity.vo.MapDataVO;

import reactor.core.publisher.Mono;

/**
 * 用户关注业务接口，定义关注与取关、关注与粉丝列表分页查询、关注数粉丝数统计、趋势分析及Neo4j同步数据获取等响应式操作
 */
public interface FocusService {
    /**
     * 让用户关注目标用户，已关注时返回 false
     */
    Mono<Boolean> addFocus(Long userId, Long focusId);

    /**
     * 取消用户对目标用户的关注，未关注时返回 false
     */
    Mono<Boolean> removeFocus(Long userId, Long focusId);

    /**
     * 查询用户是否已关注目标用户
     */
    Mono<Boolean> isFocused(Long userId, Long focusId);

    /**
     * 分页查询用户的关注列表并补充被关注用户信息
     */
    Mono<PageDTO<FocusUserVO>> listUserFocuses(Long userId, long page, long size);

    /**
     * 分页查询用户的粉丝列表并补充粉丝用户信息
     */
    Mono<PageDTO<FocusUserVO>> listUserFollowers(Long userId, long page, long size);

    /**
     * 统计用户的关注数
     */
    Mono<Long> getFocusCountByUserId(Long userId);

    /**
     * 统计用户的粉丝数
     */
    Mono<Long> getFollowerCountByUserId(Long userId);

    /**
     * 批量统计多个用户的粉丝数
     */
    Mono<BatchCountVO> getFollowCountsByUserIds(java.util.Collection<Long> userIds);

    /**
     * 获取指定时间段内的新增粉丝数
     */
    Mono<Long> getFollowersInPeriod(Long userId, LocalDateTime startDate, LocalDateTime endDate);

    /**
     * 获取指定时间段内每天的关注数
     */
    Mono<MapDataVO> getDailyFollows(Long userId, LocalDateTime startDate, LocalDateTime endDate);

    /**
     * 获取用户的总关注数
     */
    Mono<Long> getTotalFollows(Long userId);

    /**
     * 获取关注数据，用于Neo4j同步
     *
     * @param updatedAfter
     *                         增量同步时间（ISO格式），为空则全量
     */
    Mono<List<FocusSyncVO>> getNeo4jSyncFocus(String updatedAfter);
}

package com.hcsy.spring.api.service.impl;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.Collection;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.function.Function;
import java.util.stream.Collectors;

import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;
import org.springframework.transaction.reactive.TransactionalOperator;

import com.hcsy.spring.api.repository.FocusRepository;
import com.hcsy.spring.api.repository.UserRepository;
import com.hcsy.spring.api.service.FocusService;
import com.hcsy.spring.common.constants.HttpCode;
import com.hcsy.spring.common.constants.Messages;
import com.hcsy.spring.common.exceptions.BusinessException;
import com.hcsy.spring.common.utils.Neo4jSyncMapUtil;
import com.hcsy.spring.core.annotation.ArticleSync;
import com.hcsy.spring.entity.dto.PageDTO;
import com.hcsy.spring.entity.po.Focus;
import com.hcsy.spring.entity.po.User;
import com.hcsy.spring.entity.vo.BatchCountVO;
import com.hcsy.spring.entity.vo.FocusUserVO;
import com.hcsy.spring.entity.vo.IdCountVO;
import com.hcsy.spring.entity.vo.MapDataVO;

import cn.hutool.core.bean.BeanUtil;
import lombok.RequiredArgsConstructor;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

@Service
@RequiredArgsConstructor
public class FocusServiceImpl implements FocusService {

    private final FocusRepository focusRepository;
    private final UserRepository userRepository;
    private final TransactionalOperator transactionalOperator;

    @Override
    @ArticleSync(action = "focus", description = "关注了1个用户")
    public Mono<Boolean> addFocus(Long userId, Long focusId) {
        Mono<Boolean> operation = focusRepository.existsByUserIdAndFocusId(userId, focusId)
            .flatMap(exists -> {
                if (exists) {
                    return Mono.just(false);
                }
                Focus focus = new Focus();
                focus.setUserId(userId);
                focus.setFocusId(focusId);
                focus.setCreatedTime(LocalDateTime.now());
                return focusRepository.save(focus).thenReturn(true);
            });
        return transactionalOperator.transactional(operation);
    }

    @Override
    @ArticleSync(action = "unfocus", description = "取消关注了1个用户")
    public Mono<Boolean> removeFocus(Long userId, Long focusId) {
        return transactionalOperator.transactional(
            focusRepository.existsByUserIdAndFocusId(userId, focusId)
                .flatMap(exists -> exists
                    ? focusRepository.deleteByUserIdAndFocusId(userId, focusId).thenReturn(true)
                    : Mono.just(false)));
    }

    @Override
    public Mono<Boolean> isFocused(Long userId, Long focusId) {
        return focusRepository.existsByUserIdAndFocusId(userId, focusId);
    }

    @Override
    public Mono<PageDTO<FocusUserVO>> listUserFocuses(Long userId, long page, long size) {
        Flux<Focus> query = focusRepository.findByUserIdOrderByCreatedTimeDesc(userId, pageRequest(page, size));
        return buildPage(query, focusRepository.countByUserId(userId), page, size, Focus::getFocusId);
    }

    @Override
    public Mono<PageDTO<FocusUserVO>> listUserFollowers(Long userId, long page, long size) {
        Flux<Focus> query = focusRepository.findByFocusIdOrderByCreatedTimeDesc(userId, pageRequest(page, size));
        return buildPage(query, focusRepository.countByFocusId(userId), page, size, Focus::getUserId);
    }

    @Override
    public Mono<Long> getFocusCountByUserId(Long userId) {
        return focusRepository.countByUserId(userId);
    }

    @Override
    public Mono<Long> getFollowerCountByUserId(Long userId) {
        return focusRepository.countByFocusId(userId);
    }

    @Override
    public Mono<BatchCountVO> getFollowCountsByUserIds(Collection<Long> userIds) {
        if (userIds == null || userIds.isEmpty()) {
            return Mono.just(new BatchCountVO(List.of()));
        }
        return focusRepository.countGroupByFocusIdIn(userIds)
            .map(row -> new IdCountVO(row.getId(), row.getCount()))
            .collectList()
            .map(BatchCountVO::new);
    }

    private Mono<PageDTO<FocusUserVO>> buildPage(
        Flux<Focus> query,
        Mono<Long> total,
        long page,
        long size,
        Function<Focus, Long> relatedUserId) {
        Mono<List<FocusUserVO>> records = query.collectList().flatMap(focuses -> {
            Set<Long> userIds = focuses.stream().map(relatedUserId).collect(Collectors.toSet());
            return userRepository.findAllById(userIds)
                .collectMap(User::getId, Function.identity())
                .map(users -> toVOs(focuses, users, relatedUserId));
        });
        return Mono.zip(records, total).map(result -> {
            PageDTO<FocusUserVO> pageDTO = new PageDTO<>();
            pageDTO.setCurrent(page);
            pageDTO.setSize(size);
            pageDTO.setTotal(result.getT2());
            pageDTO.setRecords(result.getT1());
            return pageDTO;
        });
    }

    private List<FocusUserVO> toVOs(
        List<Focus> focuses,
        Map<Long, User> users,
        Function<Focus, Long> relatedUserId) {
        return focuses.stream().map(focus -> {
            User user = users.get(relatedUserId.apply(focus));
            if (user == null) {
                throw BusinessException.builder().httpStatus(HttpCode.NOT_FOUND)
                    .errorMessage(Messages.UNDEFINED_USER).build();
            }
            FocusUserVO vo = BeanUtil.copyProperties(user, FocusUserVO.class);
            vo.setFocusedTime(focus.getCreatedTime());
            return vo;
        }).toList();
    }

    private PageRequest pageRequest(long page, long size) {
        return PageRequest.of((int) Math.max(0, page - 1), (int) Math.max(1, Math.min(size, 1000)));
    }

    // ==================== 统计方法 ====================

    @Override
    public Mono<Long> getFollowersInPeriod(Long userId, LocalDateTime startDate, LocalDateTime endDate) {
        return focusRepository.countFollowersInPeriod(userId, startDate, endDate).defaultIfEmpty(0L);
    }

    @Override
    public Mono<MapDataVO> getDailyFollows(Long userId, LocalDateTime startDate, LocalDateTime endDate) {
        return focusRepository.countDailyFollowsByUserIdAndPeriod(userId, startDate, endDate)
            .map(row -> {
                Map<String, Object> daily = new HashMap<>();
                daily.put("date", row.getDate().toString());
                daily.put("count", row.getCount());
                return daily;
            })
            .collectList()
            .map(list -> {
                Map<String, Object> result = new HashMap<>();
                result.put("daily_follows", list);
                return new MapDataVO(result);
            });
    }

    @Override
    public Mono<Long> getTotalFollows(Long userId) {
        return focusRepository.countTotalFollowsByUserId(userId).defaultIfEmpty(0L);
    }

    @Override
    public Mono<MapDataVO> getMonthlyFollowTrend(Long userId) {
        LocalDate today = LocalDate.now();
        LocalDateTime firstDay = today.withDayOfMonth(1).atStartOfDay();
        LocalDateTime lastDay;
        if (today.getMonthValue() == 12) {
            lastDay = LocalDate.of(today.getYear() + 1, 1, 1).atStartOfDay();
        } else {
            lastDay = LocalDate.of(today.getYear(), today.getMonthValue() + 1, 1).atStartOfDay();
        }

        return focusRepository.countMonthlyByUserIdGroupByDate(userId, firstDay, lastDay)
            .map(row -> {
                Map<String, Object> trend = new HashMap<>();
                trend.put("date", row.getDate().toString());
                trend.put("count", row.getCount());
                return trend;
            })
            .collectList()
            .map(dailyTrends -> {
                Map<String, Object> result = new HashMap<>();
                result.put("daily_trends", dailyTrends);
                long total = dailyTrends.stream()
                    .mapToLong(t -> ((Number) t.get("count")).longValue())
                    .sum();
                result.put("total", total);
                return new MapDataVO(result);
            });
    }

    @Override
    public Mono<List<Map<String, Object>>> getNeo4jSyncFocus(String updatedAfter) {
        // 关注表数据量较大，全量同步仅取最近 NEO4J_SYNC_LIMIT 条，
        // 避免一次性加载全部导致耗时过长、连接/令牌超时。
        if (updatedAfter == null || updatedAfter.isBlank()) {
            return focusRepository.findLatestForSync(Neo4jSyncMapUtil.NEO4J_SYNC_LIMIT)
                .map(Neo4jSyncMapUtil::focusToMap)
                .collectList()
                .map(list -> list.isEmpty() ? new ArrayList<>() : list);
        }
        LocalDateTime after = LocalDateTime.parse(updatedAfter);
        return focusRepository.findLatestAfterForSync(after, Neo4jSyncMapUtil.NEO4J_SYNC_LIMIT)
            .map(Neo4jSyncMapUtil::focusToMap)
            .collectList()
            .map(list -> list.isEmpty() ? new ArrayList<>() : list);
    }
}

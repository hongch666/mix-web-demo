package com.hcsy.spring.api.service.impl;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.Collection;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.function.Function;
import java.util.stream.Collectors;

import org.springframework.data.domain.PageRequest;
import org.springframework.r2dbc.core.DatabaseClient;
import org.springframework.stereotype.Service;
import org.springframework.transaction.reactive.TransactionalOperator;

import com.hcsy.spring.api.repository.FocusRepository;
import com.hcsy.spring.api.repository.UserRepository;
import com.hcsy.spring.api.service.FocusService;
import com.hcsy.spring.common.constants.HttpCode;
import com.hcsy.spring.common.constants.Messages;
import com.hcsy.spring.common.exceptions.BusinessException;
import com.hcsy.spring.core.annotation.ArticleSync;
import com.hcsy.spring.entity.dto.PageDTO;
import com.hcsy.spring.entity.po.Focus;
import com.hcsy.spring.entity.po.User;
import com.hcsy.spring.entity.vo.FocusUserVO;

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
    private final DatabaseClient databaseClient;

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
    public Mono<Map<Long, Long>> getFollowCountsByUserIds(Collection<Long> userIds) {
        if (userIds == null || userIds.isEmpty()) {
            return Mono.just(Map.of());
        }
        return Flux.fromIterable(userIds)
            .flatMap(id -> focusRepository.countByFocusId(id)
                .map(count -> Map.entry(id, count)))
            .collectMap(Map.Entry::getKey, Map.Entry::getValue);
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
        String sql = """
            SELECT COUNT(*) FROM focus
            WHERE focus_id = :userId AND created_time >= :startDate AND created_time <= :endDate
            """;
        return databaseClient.sql(sql)
            .bind("userId", userId)
            .bind("startDate", startDate)
            .bind("endDate", endDate)
            .map((row, metadata) -> row.get(0, Long.class))
            .one()
            .defaultIfEmpty(0L);
    }

    @Override
    public Mono<Map<String, Object>> getDailyFollows(Long userId, LocalDateTime startDate, LocalDateTime endDate) {
        String sql = """
            SELECT DATE(created_time) as date, COUNT(*) as count
            FROM focus
            WHERE user_id = :userId AND created_time >= :startDate AND created_time <= :endDate
            GROUP BY DATE(created_time)
            ORDER BY DATE(created_time)
            """;
        return databaseClient.sql(sql)
            .bind("userId", userId)
            .bind("startDate", startDate)
            .bind("endDate", endDate)
            .map((row, metadata) -> {
                Map<String, Object> daily = new HashMap<>();
                daily.put("date", row.get("date").toString());
                daily.put("count", row.get("count"));
                return daily;
            })
            .all()
            .collectList()
            .map(list -> {
                Map<String, Object> result = new HashMap<>();
                result.put("daily_follows", list);
                return result;
            });
    }

    @Override
    public Mono<Long> getTotalFollows(Long userId) {
        String sql = "SELECT COUNT(*) FROM focus WHERE user_id = :userId";
        return databaseClient.sql(sql)
            .bind("userId", userId)
            .map((row, metadata) -> row.get(0, Long.class))
            .one()
            .defaultIfEmpty(0L);
    }

    @Override
    public Mono<Map<String, Object>> getMonthlyFollowTrend(Long userId) {
        LocalDate today = LocalDate.now();
        LocalDateTime firstDay = today.withDayOfMonth(1).atStartOfDay();
        LocalDateTime lastDay;
        if (today.getMonthValue() == 12) {
            lastDay = LocalDate.of(today.getYear() + 1, 1, 1).atStartOfDay();
        } else {
            lastDay = LocalDate.of(today.getYear(), today.getMonthValue() + 1, 1).atStartOfDay();
        }

        String sql = """
            SELECT DATE(created_time) as date, COUNT(*) as count
            FROM focus
            WHERE user_id = :userId AND created_time >= :firstDay AND created_time < :lastDay
            GROUP BY DATE(created_time)
            ORDER BY DATE(created_time)
            """;

        return databaseClient.sql(sql)
            .bind("userId", userId)
            .bind("firstDay", firstDay)
            .bind("lastDay", lastDay)
            .map((row, metadata) -> {
                Map<String, Object> trend = new HashMap<>();
                trend.put("date", row.get("date").toString());
                trend.put("count", row.get("count"));
                return trend;
            })
            .all()
            .collectList()
            .map(dailyTrends -> {
                Map<String, Object> result = new HashMap<>();
                result.put("daily_trends", dailyTrends);
                long total = dailyTrends.stream()
                    .mapToLong(t -> ((Number) t.get("count")).longValue())
                    .sum();
                result.put("total", total);
                return result;
            });
    }
}

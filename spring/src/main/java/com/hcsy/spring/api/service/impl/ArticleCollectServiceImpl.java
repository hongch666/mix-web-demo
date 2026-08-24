package com.hcsy.spring.api.service.impl;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.Collection;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;
import org.springframework.transaction.reactive.TransactionalOperator;

import com.hcsy.spring.api.repository.ArticleCollectRepository;
import com.hcsy.spring.api.service.ArticleCollectService;
import com.hcsy.spring.api.service.ArticleService;
import com.hcsy.spring.common.utils.Neo4jSyncMapUtil;
import com.hcsy.spring.core.annotation.ArticleSync;
import com.hcsy.spring.entity.dto.PageDTO;
import com.hcsy.spring.entity.po.ArticleCollect;
import com.hcsy.spring.entity.vo.ArticleCollectVO;

import lombok.RequiredArgsConstructor;
import reactor.core.publisher.Mono;

@Service
@RequiredArgsConstructor
public class ArticleCollectServiceImpl implements ArticleCollectService {

    private final ArticleCollectRepository articleCollectRepository;
    private final ArticleInteractionAssembler assembler;
    private final TransactionalOperator transactionalOperator;
    private final ArticleService articleService;

    @Override
    @ArticleSync(action = "collect", description = "收藏了1篇文章")
    public Mono<Boolean> addCollect(Long articleId, Long userId) {
        Mono<Boolean> operation = articleCollectRepository.existsByArticleIdAndUserId(articleId, userId)
            .flatMap(exists -> {
                if (exists) {
                    return Mono.just(false);
                }
                ArticleCollect collect = new ArticleCollect();
                collect.setArticleId(articleId);
                collect.setUserId(userId);
                collect.setCreatedTime(LocalDateTime.now());
                return articleCollectRepository.save(collect).thenReturn(true);
            });
        return transactionalOperator.transactional(operation);
    }

    @Override
    @ArticleSync(action = "uncollect", description = "取消收藏了1篇文章")
    public Mono<Boolean> removeCollect(Long articleId, Long userId) {
        return transactionalOperator.transactional(
            articleCollectRepository.existsByArticleIdAndUserId(articleId, userId)
                .flatMap(exists -> exists
                    ? articleCollectRepository.deleteByArticleIdAndUserId(articleId, userId)
                        .thenReturn(true)
                    : Mono.just(false)));
    }

    @Override
    public Mono<Boolean> isCollected(Long articleId, Long userId) {
        return articleCollectRepository.existsByArticleIdAndUserId(articleId, userId);
    }

    @Override
    public Mono<PageDTO<ArticleCollectVO>> listUserCollects(Long userId, long page, long size) {
        Mono<List<ArticleCollectVO>> records = articleCollectRepository
            .findByUserIdOrderByCreatedTimeDesc(userId, pageRequest(page, size))
            .collectList()
            .flatMap(assembler::toCollectVOs);
        return Mono.zip(records, articleCollectRepository.countByUserId(userId))
            .map(result -> page(page, size, result.getT2(), result.getT1()));
    }

    @Override
    public Mono<Long> getCollectCountByArticleId(Long articleId) {
        return articleCollectRepository.countByArticleId(articleId);
    }

    @Override
    public Mono<Map<Long, Long>> getCollectCountsByArticleIds(Collection<Long> articleIds) {
        if (articleIds == null || articleIds.isEmpty()) {
            return Mono.just(Map.of());
        }
        return articleCollectRepository.countGroupByArticleIdIn(articleIds)
            .collectMap(
                row -> ((Number) row.get("article_id")).longValue(),
                row -> ((Number) row.get("cnt")).longValue());
    }

    private PageRequest pageRequest(long page, long size) {
        return PageRequest.of((int) Math.max(0, page - 1), (int) Math.max(1, Math.min(size, 1000)));
    }

    private PageDTO<ArticleCollectVO> page(long current, long size, long total, List<ArticleCollectVO> records) {
        PageDTO<ArticleCollectVO> result = new PageDTO<>();
        result.setCurrent(current);
        result.setSize(size);
        result.setTotal(total);
        result.setRecords(records);
        return result;
    }

    // ==================== 统计方法 ====================

    @Override
    public Mono<Long> getTotalCollects() {
        return articleCollectRepository.count();
    }

    @Override
    public Mono<Double> getAverageCollects() {
        return Mono.zip(articleService.getTotalArticles(), getTotalCollects())
            .flatMap(result -> {
                long totalArticles = result.getT1();
                long totalCollects = result.getT2();
                if (totalArticles == 0) {
                    return Mono.just(0.0);
                }
                return Mono.just(Math.round(totalCollects * 100.0 / totalArticles) / 100.0);
            });
    }

    @Override
    public Mono<Map<String, Object>> getMonthlyCollectTrend(Long userId) {
        LocalDate today = LocalDate.now();
        LocalDateTime firstDay = today.withDayOfMonth(1).atStartOfDay();
        LocalDateTime lastDay;
        if (today.getMonthValue() == 12) {
            lastDay = LocalDate.of(today.getYear() + 1, 1, 1).atStartOfDay();
        } else {
            lastDay = LocalDate.of(today.getYear(), today.getMonthValue() + 1, 1).atStartOfDay();
        }

        return articleCollectRepository.countMonthlyByUserIdGroupByDate(userId, firstDay, lastDay)
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
                return result;
            });
    }

    @Override
    public Mono<List<Map<String, Object>>> getNeo4jSyncCollects(String updatedAfter) {
        // 收藏表数据量可达百万级，全量同步仅取最近 NEO4J_SYNC_LIMIT 条，
        // 避免一次性加载全部导致耗时过长、连接/令牌超时。
        if (updatedAfter == null || updatedAfter.isBlank()) {
            return articleCollectRepository.findLatestForSync(Neo4jSyncMapUtil.NEO4J_SYNC_LIMIT)
                .map(Neo4jSyncMapUtil::collectToMap)
                .collectList()
                .map(list -> list.isEmpty() ? new ArrayList<>() : list);
        }
        LocalDateTime after = LocalDateTime.parse(updatedAfter);
        return articleCollectRepository.findLatestAfterForSync(after, Neo4jSyncMapUtil.NEO4J_SYNC_LIMIT)
            .map(Neo4jSyncMapUtil::collectToMap)
            .collectList()
            .map(list -> list.isEmpty() ? new ArrayList<>() : list);
    }
}

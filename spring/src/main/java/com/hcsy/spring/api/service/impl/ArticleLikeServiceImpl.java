package com.hcsy.spring.api.service.impl;

import com.hcsy.spring.common.constants.Defaults;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.Collection;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;
import org.springframework.transaction.reactive.TransactionalOperator;

import com.hcsy.spring.api.repository.ArticleLikeRepository;
import com.hcsy.spring.api.service.ArticleLikeService;
import com.hcsy.spring.api.service.ArticleService;
import com.hcsy.spring.core.annotation.ArticleSync;
import com.hcsy.spring.entity.dto.PageDTO;
import com.hcsy.spring.entity.po.ArticleLike;
import com.hcsy.spring.entity.vo.ArticleLikeVO;
import com.hcsy.spring.entity.vo.BatchCountVO;
import com.hcsy.spring.entity.vo.IdCountVO;
import com.hcsy.spring.entity.vo.MapDataVO;

import lombok.RequiredArgsConstructor;
import reactor.core.publisher.Mono;

@Service
@RequiredArgsConstructor
public class ArticleLikeServiceImpl implements ArticleLikeService {

    private final ArticleLikeRepository articleLikeRepository;
    private final ArticleInteractionAssembler assembler;
    private final TransactionalOperator transactionalOperator;
    private final ArticleService articleService;

    @Override
    @ArticleSync(action = "like", description = "点赞了1篇文章")
    public Mono<Boolean> addLike(Long articleId, Long userId) {
        Mono<Boolean> operation = articleLikeRepository.existsByArticleIdAndUserId(articleId, userId)
            .flatMap(exists -> {
                if (exists) {
                    return Mono.just(false);
                }
                ArticleLike like = new ArticleLike();
                like.setArticleId(articleId);
                like.setUserId(userId);
                like.setCreatedTime(LocalDateTime.now());
                return articleLikeRepository.save(like).thenReturn(true);
            });
        return transactionalOperator.transactional(operation);
    }

    @Override
    @ArticleSync(action = "unlike", description = "取消点赞了1篇文章")
    public Mono<Boolean> removeLike(Long articleId, Long userId) {
        return transactionalOperator.transactional(
            articleLikeRepository.existsByArticleIdAndUserId(articleId, userId)
                .flatMap(exists -> exists
                    ? articleLikeRepository.deleteByArticleIdAndUserId(articleId, userId).thenReturn(true)
                    : Mono.just(false)));
    }

    @Override
    public Mono<Boolean> isLiked(Long articleId, Long userId) {
        return articleLikeRepository.existsByArticleIdAndUserId(articleId, userId);
    }

    @Override
    public Mono<PageDTO<ArticleLikeVO>> listUserLikes(Long userId, long page, long size) {
        Mono<List<ArticleLikeVO>> records = articleLikeRepository
            .findByUserIdOrderByCreatedTimeDesc(userId, pageRequest(page, size))
            .collectList()
            .flatMap(assembler::toLikeVOs);
        return Mono.zip(records, articleLikeRepository.countByUserId(userId))
            .map(result -> page(page, size, result.getT2(), result.getT1()));
    }

    @Override
    public Mono<Long> getLikeCountByArticleId(Long articleId) {
        return articleLikeRepository.countByArticleId(articleId);
    }

    @Override
    public Mono<BatchCountVO> getLikeCountsByArticleIds(Collection<Long> articleIds) {
        if (articleIds == null || articleIds.isEmpty()) {
            return Mono.just(new BatchCountVO(List.of()));
        }
        return articleLikeRepository.countGroupByArticleIdIn(articleIds)
            .map(row -> new IdCountVO(row.getId(), row.getCount()))
            .collectList()
            .map(BatchCountVO::new);
    }

    private PageRequest pageRequest(long page, long size) {
        return PageRequest.of((int) Math.max(0, page - 1), (int) Math.max(1, Math.min(size, 1000)));
    }

    private PageDTO<ArticleLikeVO> page(long current, long size, long total, List<ArticleLikeVO> records) {
        PageDTO<ArticleLikeVO> result = new PageDTO<>();
        result.setCurrent(current);
        result.setSize(size);
        result.setTotal(total);
        result.setRecords(records);
        return result;
    }

    // ==================== 统计方法 ====================

    @Override
    public Mono<Long> getTotalLikes() {
        return articleLikeRepository.count();
    }

    @Override
    public Mono<Double> getAverageLikes() {
        return Mono.zip(articleService.getTotalArticles(), getTotalLikes())
            .flatMap(result -> {
                long totalArticles = result.getT1();
                long totalLikes = result.getT2();
                if (totalArticles == 0) {
                    return Mono.just(0.0);
                }
                return Mono.just(Math.round(totalLikes * 100.0 / totalArticles) / 100.0);
            });
    }

    @Override
    public Mono<MapDataVO> getMonthlyLikeTrend(Long userId) {
        LocalDate today = LocalDate.now();
        LocalDateTime firstDay = today.withDayOfMonth(1).atStartOfDay();
        LocalDateTime lastDay;
        if (today.getMonthValue() == 12) {
            lastDay = LocalDate.of(today.getYear() + 1, 1, 1).atStartOfDay();
        } else {
            lastDay = LocalDate.of(today.getYear(), today.getMonthValue() + 1, 1).atStartOfDay();
        }

        return articleLikeRepository.countMonthlyByUserIdGroupByDate(userId, firstDay, lastDay)
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
    public Mono<List<Map<String, Object>>> getNeo4jSyncLikes(String updatedAfter) {
        // 点赞表数据量可达百万级，全量同步仅取最近 NEO4J_SYNC_LIMIT 条，
        // 避免一次性加载全部导致耗时过长、连接/令牌超时。
        if (updatedAfter == null || updatedAfter.isBlank()) {
            return articleLikeRepository.findLatestForSync(Defaults.NEO4J_SYNC_LIMIT)
                .map(this::likeToMap)
                .collectList()
                .map(list -> list.isEmpty() ? new ArrayList<>() : list);
        }
        LocalDateTime after = LocalDateTime.parse(updatedAfter);
        return articleLikeRepository.findLatestAfterForSync(after, Defaults.NEO4J_SYNC_LIMIT)
            .map(this::likeToMap)
            .collectList()
            .map(list -> list.isEmpty() ? new ArrayList<>() : list);
    }

    /**
     * 点赞实体转 Map，字段名与数据库列名保持一致，用于 Neo4j 同步
     */
    private Map<String, Object> likeToMap(ArticleLike like) {
        Map<String, Object> map = new LinkedHashMap<>();
        map.put("user_id", like.getUserId());
        map.put("article_id", like.getArticleId());
        map.put("created_time", like.getCreatedTime());
        return map;
    }
}

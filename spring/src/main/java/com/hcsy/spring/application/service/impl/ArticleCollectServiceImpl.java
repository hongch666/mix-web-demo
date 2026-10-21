package com.hcsy.spring.application.service.impl;

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

import com.hcsy.spring.application.service.ArticleCollectService;
import com.hcsy.spring.application.service.ArticleService;
import com.hcsy.spring.common.constants.Defaults;
import com.hcsy.spring.entity.assembler.ArticleInteractionAssembler;
import com.hcsy.spring.entity.dto.PageDTO;
import com.hcsy.spring.entity.po.ArticleCollect;
import com.hcsy.spring.entity.vo.ArticleCollectVO;
import com.hcsy.spring.entity.vo.ArticleRelationSyncVO;
import com.hcsy.spring.entity.vo.BatchCountVO;
import com.hcsy.spring.entity.vo.MapDataVO;
import com.hcsy.spring.infra.repository.ArticleCollectRepository;

import lombok.RequiredArgsConstructor;
import reactor.core.publisher.Mono;

/**
 * ArticleCollectService 的实现，在事务中完成文章收藏的查重写入与取消删除，并组装收藏分页视图与各类收藏统计数据
 */
@Service
@RequiredArgsConstructor
public class ArticleCollectServiceImpl implements ArticleCollectService {

    private final ArticleCollectRepository articleCollectRepository;
    private final ArticleInteractionAssembler assembler;
    private final TransactionalOperator transactionalOperator;
    private final ArticleService articleService;

    /**
     * 实现收藏文章，在事务中查重后写入收藏记录，已存在返回 false
     */
    @Override
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

    /**
     * 实现取消收藏，在事务中确认存在后删除，未收藏返回 false
     */
    @Override
    public Mono<Boolean> removeCollect(Long articleId, Long userId) {
        return transactionalOperator.transactional(
            articleCollectRepository.existsByArticleIdAndUserId(articleId, userId)
                .flatMap(exists -> exists
                    ? articleCollectRepository.deleteByArticleIdAndUserId(articleId, userId)
                        .thenReturn(true)
                    : Mono.just(false)));
    }

    /**
     * 实现查询用户是否已收藏指定文章
     */
    @Override
    public Mono<Boolean> isCollected(Long articleId, Long userId) {
        return articleCollectRepository.existsByArticleIdAndUserId(articleId, userId);
    }

    /**
     * 实现分页查询用户收藏列表，组装收藏视图与总数
     */
    @Override
    public Mono<PageDTO<ArticleCollectVO>> listUserCollects(Long userId, long page, long size) {
        Mono<List<ArticleCollectVO>> records = articleCollectRepository
            .findByUserIdOrderByCreatedTimeDesc(userId, pageRequest(page, size))
            .collectList()
            .flatMap(assembler::toCollectVOs);
        return Mono.zip(records, articleCollectRepository.countByUserId(userId))
            .map(result -> page(page, size, result.getT2(), result.getT1()));
    }

    /**
     * 实现统计指定文章的收藏总数
     */
    @Override
    public Mono<Long> getCollectCountByArticleId(Long articleId) {
        return articleCollectRepository.countByArticleId(articleId);
    }

    /**
     * 实现按文章ID分组批量统计收藏数
     */
    @Override
    public Mono<BatchCountVO> getCollectCountsByArticleIds(Collection<Long> articleIds) {
        if (articleIds == null || articleIds.isEmpty()) {
            return Mono.just(new BatchCountVO(List.of()));
        }
        // 具体类投影：接口投影（IdCountRow）映射不出 count 列，会静默返回 null 导致计数为 0
        return articleCollectRepository.countGroupByArticleIdIn(articleIds)
            .collectList()
            .map(BatchCountVO::new);
    }

    /**
     * 构造分页请求，页码从1起始转0起始并限制每页最大1000条
     */
    private PageRequest pageRequest(long page, long size) {
        return PageRequest.of((int) Math.max(0, page - 1), (int) Math.max(1, Math.min(size, 1000)));
    }

    /**
     * 组装收藏分页结果的当前页、页大小、总数与记录
     */
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

    /**
     * 实现计算每篇文章的平均收藏数，结果保留两位小数
     */
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

    /**
     * 实现统计用户本月每日收藏趋势与总数
     */
    @Override
    public Mono<MapDataVO> getMonthlyCollectTrend(Long userId) {
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
                return new MapDataVO(result);
            });
    }

    /**
     * 实现查询收藏关系数据用于Neo4j同步，全量时仅取最近限定条数
     */
    @Override
    public Mono<List<ArticleRelationSyncVO>> getNeo4jSyncCollects(String updatedAfter) {
        // 收藏表数据量可达百万级，全量同步仅取最近 NEO4J_SYNC_LIMIT 条，避免一次性加载全部导致耗时过长、连接/令牌超时
        if (updatedAfter == null || updatedAfter.isBlank()) {
            return articleCollectRepository.findLatestForSync(Defaults.NEO4J_SYNC_LIMIT)
                .map(this::collectToVO)
                .collectList()
                .map(list -> list.isEmpty() ? new ArrayList<>() : list);
        }
        LocalDateTime after = LocalDateTime.parse(updatedAfter);
        return articleCollectRepository.findLatestAfterForSync(after, Defaults.NEO4J_SYNC_LIMIT)
            .map(this::collectToVO)
            .collectList()
            .map(list -> list.isEmpty() ? new ArrayList<>() : list);
    }

    /**
     * 收藏实体转同步视图对象，字段名与数据库列名保持一致，用于 Neo4j 同步
     */
    private ArticleRelationSyncVO collectToVO(ArticleCollect collect) {
        return new ArticleRelationSyncVO(collect.getUserId(), collect.getArticleId(), collect.getCreatedTime());
    }
}

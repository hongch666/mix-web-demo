package com.hcsy.spring.api.service;

import java.util.List;
import java.util.Map;

import com.hcsy.spring.entity.dto.PageDTO;
import com.hcsy.spring.entity.vo.ArticleCollectVO;

import reactor.core.publisher.Mono;

public interface ArticleCollectService {
    Mono<Boolean> addCollect(Long articleId, Long userId);

    Mono<Boolean> removeCollect(Long articleId, Long userId);

    Mono<Boolean> isCollected(Long articleId, Long userId);

    Mono<PageDTO<ArticleCollectVO>> listUserCollects(Long userId, long page, long size);

    Mono<Long> getCollectCountByArticleId(Long articleId);

    Mono<Map<Long, Long>> getCollectCountsByArticleIds(java.util.Collection<Long> articleIds);

    /**
     * 获取所有文章的总收藏数
     */
    Mono<Long> getTotalCollects();

    /**
     * 获取每篇文章的平均收藏数
     */
    Mono<Double> getAverageCollects();

    /**
     * 获取用户本月收藏的趋势
     */
    Mono<Map<String, Object>> getMonthlyCollectTrend(Long userId);

    /**
     * 获取收藏数据，用于Neo4j同步
     *
     * @param updatedAfter
     *                         增量同步时间（ISO格式），为空则全量
     */
    Mono<List<Map<String, Object>>> getNeo4jSyncCollects(String updatedAfter);
}

package com.hcsy.spring.api.service;

import java.util.List;
import java.util.Map;

import com.hcsy.spring.entity.dto.PageDTO;
import com.hcsy.spring.entity.vo.ArticleLikeVO;

import reactor.core.publisher.Mono;

public interface ArticleLikeService {
    Mono<Boolean> addLike(Long articleId, Long userId);

    Mono<Boolean> removeLike(Long articleId, Long userId);

    Mono<Boolean> isLiked(Long articleId, Long userId);

    Mono<PageDTO<ArticleLikeVO>> listUserLikes(Long userId, long page, long size);

    Mono<Long> getLikeCountByArticleId(Long articleId);

    Mono<Map<Long, Long>> getLikeCountsByArticleIds(java.util.Collection<Long> articleIds);

    /**
     * 获取所有文章的总点赞数
     */
    Mono<Long> getTotalLikes();

    /**
     * 获取每篇文章的平均点赞数
     */
    Mono<Double> getAverageLikes();

    /**
     * 获取用户本月点赞的趋势
     */
    Mono<Map<String, Object>> getMonthlyLikeTrend(Long userId);

    /**
     * 获取点赞数据，用于Neo4j同步
     *
     * @param updatedAfter
     *                         增量同步时间（ISO格式），为空则全量
     */
    Mono<List<Map<String, Object>>> getNeo4jSyncLikes(String updatedAfter);
}

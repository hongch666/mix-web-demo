package com.hcsy.spring.application.service;

import java.util.List;

import com.hcsy.spring.entity.dto.PageDTO;
import com.hcsy.spring.entity.vo.ArticleCollectVO;
import com.hcsy.spring.entity.vo.ArticleRelationSyncVO;
import com.hcsy.spring.entity.vo.BatchCountVO;
import com.hcsy.spring.entity.vo.MapDataVO;

import reactor.core.publisher.Mono;

/**
 * 文章收藏业务接口，定义收藏与取消收藏、收藏状态与列表分页查询、收藏数统计及Neo4j同步数据获取等响应式操作
 */
public interface ArticleCollectService {
    /**
     * 为用户收藏指定文章，已收藏时返回 false
     */
    Mono<Boolean> addCollect(Long articleId, Long userId);

    /**
     * 取消用户对指定文章的收藏，未收藏时返回 false
     */
    Mono<Boolean> removeCollect(Long articleId, Long userId);

    /**
     * 查询用户是否已收藏指定文章
     */
    Mono<Boolean> isCollected(Long articleId, Long userId);

    /**
     * 分页查询用户的收藏列表并组装收藏视图
     */
    Mono<PageDTO<ArticleCollectVO>> listUserCollects(Long userId, long page, long size);

    /**
     * 统计指定文章的收藏总数
     */
    Mono<Long> getCollectCountByArticleId(Long articleId);

    /**
     * 批量统计多篇文章的收藏数，按文章ID返回计数列表
     */
    Mono<BatchCountVO> getCollectCountsByArticleIds(java.util.Collection<Long> articleIds);

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
    Mono<MapDataVO> getMonthlyCollectTrend(Long userId);

    /**
     * 获取收藏数据，用于Neo4j同步
     *
     * @param updatedAfter
     *                         增量同步时间（ISO格式），为空则全量
     */
    Mono<List<ArticleRelationSyncVO>> getNeo4jSyncCollects(String updatedAfter);
}

package com.hcsy.spring.application.service;

import java.util.List;

import com.hcsy.spring.entity.dto.PageDTO;
import com.hcsy.spring.entity.vo.ArticleLikeVO;
import com.hcsy.spring.entity.vo.ArticleRelationSyncVO;
import com.hcsy.spring.entity.vo.BatchCountVO;
import com.hcsy.spring.entity.vo.MapDataVO;

import reactor.core.publisher.Mono;

/**
 * 文章点赞业务接口，定义点赞与取消点赞、点赞状态与列表分页查询、点赞数统计及Neo4j同步数据获取等响应式操作
 */
public interface ArticleLikeService {
    /**
     * 为用户点赞指定文章，已点赞时返回 false
     */
    Mono<Boolean> addLike(Long articleId, Long userId);

    /**
     * 取消用户对指定文章的点赞，未点赞时返回 false
     */
    Mono<Boolean> removeLike(Long articleId, Long userId);

    /**
     * 查询用户是否已点赞指定文章
     */
    Mono<Boolean> isLiked(Long articleId, Long userId);

    /**
     * 分页查询用户的点赞列表并组装点赞视图
     */
    Mono<PageDTO<ArticleLikeVO>> listUserLikes(Long userId, long page, long size);

    /**
     * 统计指定文章的点赞总数
     */
    Mono<Long> getLikeCountByArticleId(Long articleId);

    /**
     * 批量统计多篇文章的点赞数，按文章ID返回计数列表
     */
    Mono<BatchCountVO> getLikeCountsByArticleIds(java.util.Collection<Long> articleIds);

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
    Mono<MapDataVO> getMonthlyLikeTrend(Long userId);

    /**
     * 获取点赞数据，用于Neo4j同步
     *
     * @param updatedAfter
     *                         增量同步时间（ISO格式），为空则全量
     */
    Mono<List<ArticleRelationSyncVO>> getNeo4jSyncLikes(String updatedAfter);
}

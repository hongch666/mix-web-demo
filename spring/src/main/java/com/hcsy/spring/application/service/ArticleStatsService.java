package com.hcsy.spring.application.service;

import java.util.Collection;

import com.hcsy.spring.entity.vo.ArticleStatsBatchVO;

import reactor.core.publisher.Mono;

/**
 * 文章统计聚合业务接口，将阅读量、点赞、收藏、粉丝与评论评分合并为一次批量查询
 */
public interface ArticleStatsService {
    /**
     * 按文章ID与作者ID批量聚合各项统计数据
     */
    Mono<ArticleStatsBatchVO> getStatsBatch(Collection<Long> articleIds, Collection<Long> authorIds);
}

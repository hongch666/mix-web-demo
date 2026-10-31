package com.hcsy.spring.application.service.impl;

import java.util.Collection;
import java.util.List;
import java.util.Objects;

import org.springframework.stereotype.Service;

import com.hcsy.spring.application.service.ArticleStatsService;
import com.hcsy.spring.entity.assembler.CommentScoreAssembler;
import com.hcsy.spring.entity.vo.ArticleCommentScoresVO;
import com.hcsy.spring.entity.vo.ArticleStatsBatchVO;
import com.hcsy.spring.entity.vo.IdCountVO;
import com.hcsy.spring.infra.repository.ArticleCollectRepository;
import com.hcsy.spring.infra.repository.ArticleLikeRepository;
import com.hcsy.spring.infra.repository.ArticleRepository;
import com.hcsy.spring.infra.repository.FocusRepository;

import lombok.RequiredArgsConstructor;
import reactor.core.publisher.Mono;

/**
 * ArticleStatsService 的实现，并行聚合文章与作者的各项统计指标
 * 只依赖仓储与装配器，不反向依赖业务服务，避免与点赞、收藏服务形成循环依赖
 */
@Service
@RequiredArgsConstructor
public class ArticleStatsServiceImpl implements ArticleStatsService {

    private final ArticleRepository articleRepository;
    private final ArticleLikeRepository articleLikeRepository;
    private final ArticleCollectRepository articleCollectRepository;
    private final FocusRepository focusRepository;
    private final CommentScoreAssembler commentScoreAssembler;

    /**
     * 并行查询阅读量、点赞、收藏、粉丝与评论评分后合并为单个响应对象
     */
    @Override
    public Mono<ArticleStatsBatchVO> getStatsBatch(Collection<Long> articleIds, Collection<Long> authorIds) {
        List<Long> ids = normalize(articleIds);
        if (ids.isEmpty()) {
            return Mono.just(new ArticleStatsBatchVO(List.of(), List.of(), List.of(), List.of(), List.of()));
        }
        List<Long> userIds = normalize(authorIds);

        Mono<List<IdCountVO>> views = articleRepository.countViewsByIdIn(ids).collectList();
        Mono<List<IdCountVO>> likes = articleLikeRepository.countGroupByArticleIdIn(ids).collectList();
        Mono<List<IdCountVO>> collects = articleCollectRepository.countGroupByArticleIdIn(ids).collectList();
        Mono<List<IdCountVO>> follows = userIds.isEmpty()
            ? Mono.just(List.of())
            : focusRepository.countGroupByFocusIdIn(userIds).collectList();
        Mono<List<ArticleCommentScoresVO>> commentScores = commentScoreAssembler.toScoresByArticleIds(ids);

        return Mono.zip(views, likes, collects, follows, commentScores)
            .map(result -> new ArticleStatsBatchVO(result.getT1(), result.getT2(), result.getT3(),
                result.getT4(), result.getT5()));
    }

    /**
     * 去除空值与重复ID并保持顺序
     */
    private static List<Long> normalize(Collection<Long> ids) {
        if (ids == null || ids.isEmpty()) {
            return List.of();
        }
        return ids.stream().filter(Objects::nonNull).distinct().toList();
    }
}

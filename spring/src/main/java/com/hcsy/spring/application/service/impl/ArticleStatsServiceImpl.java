package com.hcsy.spring.application.service.impl;

import java.util.Collection;
import java.util.List;
import java.util.Objects;

import org.springframework.stereotype.Service;

import com.hcsy.spring.application.service.ArticleCollectService;
import com.hcsy.spring.application.service.ArticleLikeService;
import com.hcsy.spring.application.service.ArticleService;
import com.hcsy.spring.application.service.ArticleStatsService;
import com.hcsy.spring.application.service.CommentsService;
import com.hcsy.spring.application.service.FocusService;
import com.hcsy.spring.entity.vo.ArticleCommentScoresVO;
import com.hcsy.spring.entity.vo.ArticleStatsBatchVO;
import com.hcsy.spring.entity.vo.BatchCountVO;
import com.hcsy.spring.entity.vo.IdCountVO;

import lombok.RequiredArgsConstructor;
import reactor.core.publisher.Mono;

/**
 * ArticleStatsService 的实现，并行聚合文章与作者的各项统计指标
 */
@Service
@RequiredArgsConstructor
public class ArticleStatsServiceImpl implements ArticleStatsService {

    private final ArticleService articleService;
    private final ArticleLikeService articleLikeService;
    private final ArticleCollectService articleCollectService;
    private final FocusService focusService;
    private final CommentsService commentsService;

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

        Mono<List<IdCountVO>> views = articleService.getArticleViewsByIDs(ids).defaultIfEmpty(List.of());
        Mono<List<IdCountVO>> likes = articleLikeService.getLikeCountsByArticleIds(ids)
            .map(ArticleStatsServiceImpl::counts).defaultIfEmpty(List.of());
        Mono<List<IdCountVO>> collects = articleCollectService.getCollectCountsByArticleIds(ids)
            .map(ArticleStatsServiceImpl::counts).defaultIfEmpty(List.of());
        Mono<List<IdCountVO>> follows = userIds.isEmpty()
            ? Mono.just(List.of())
            : focusService.getFollowCountsByUserIds(userIds)
                .map(ArticleStatsServiceImpl::counts).defaultIfEmpty(List.of());
        Mono<List<ArticleCommentScoresVO>> commentScores = commentsService.getCommentScoresByArticleIds(ids)
            .defaultIfEmpty(List.of());

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

    /**
     * 从批量计数对象中取出计数列表，空对象返回空列表
     */
    private static List<IdCountVO> counts(BatchCountVO batchCountVO) {
        if (batchCountVO == null || batchCountVO.getCounts() == null) {
            return List.of();
        }
        return batchCountVO.getCounts();
    }
}

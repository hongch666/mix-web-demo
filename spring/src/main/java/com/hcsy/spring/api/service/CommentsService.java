package com.hcsy.spring.api.service;

import java.util.List;
import java.util.Map;

import com.hcsy.spring.entity.dto.CommentsQueryDTO;
import com.hcsy.spring.entity.dto.PageDTO;
import com.hcsy.spring.entity.po.Comments;
import com.hcsy.spring.entity.vo.ArticleCommentScoresVO;
import com.hcsy.spring.entity.vo.MapDataVO;

import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

public interface CommentsService {
    Mono<PageDTO<Comments>> listCommentsWithFilter(long page, long size, CommentsQueryDTO queryDTO);

    Mono<PageDTO<Comments>> listAICommentsWithFilter(long page, long size, CommentsQueryDTO queryDTO);

    Mono<PageDTO<Comments>> listCommentsByUserId(long page, long size, Long userId);

    Mono<PageDTO<Comments>> listCommentsByArticleId(long page, long size, Long articleId, String sortWay);

    Flux<Comments> listAICommentsByArticleId(Long articleId);

    Mono<Comments> save(Comments comments);

    Mono<Comments> update(Comments comments);

    Mono<Comments> getById(Long id);

    Mono<Void> deleteComment(Long id);

    Mono<Void> deleteComments(List<Long> ids);

    /**
     * 批量查询文章评论评分，按角色（ai/user）分组
     */
    Mono<List<ArticleCommentScoresVO>> getCommentScoresByArticleIds(
        java.util.Collection<Long> articleIds);

    /**
     * 获取文章的AI评论数
     */
    Mono<Long> getAiCommentsNumByArticleId(Long articleId);

    /**
     * 删除文章的AI评论
     */
    Mono<Void> deleteAiCommentsByArticleId(Long articleId);

    /**
     * 获取用户本月评论的趋势
     */
    Mono<MapDataVO> getMonthlyCommentTrend(Long userId);

    /**
     * 获取评论数据，用于Neo4j同步
     *
     * @param updatedAfter
     *                         增量同步时间（ISO格式），为空则全量
     */
    Mono<List<Map<String, Object>>> getNeo4jSyncComments(String updatedAfter);
}

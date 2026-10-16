package com.hcsy.spring.application.service;

import java.util.List;

import com.hcsy.spring.entity.dto.CommentCreateDTO;
import com.hcsy.spring.entity.dto.CommentUpdateDTO;
import com.hcsy.spring.entity.dto.CommentsQueryDTO;
import com.hcsy.spring.entity.dto.PageDTO;
import com.hcsy.spring.entity.po.Comments;
import com.hcsy.spring.entity.vo.AICommentsVO;
import com.hcsy.spring.entity.vo.ArticleCommentScoresVO;
import com.hcsy.spring.entity.vo.CommentSyncVO;
import com.hcsy.spring.entity.vo.CommentsVO;
import com.hcsy.spring.entity.vo.MapDataVO;
import com.hcsy.spring.entity.vo.PageVO;

import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

public interface CommentsService {
    Mono<Comments> createComment(CommentCreateDTO dto);

    Mono<Comments> updateComment(CommentUpdateDTO dto);

    Mono<CommentsVO> getCommentDetail(Long id);

    Mono<PageVO<CommentsVO>> listCommentDetails(PageDTO<Comments> page);

    Mono<List<AICommentsVO>> listAICommentDetailsByArticleId(Long articleId);

    Mono<List<CommentSyncVO>> getCommentSyncByIds(java.util.Collection<Long> ids);
    Mono<PageDTO<Comments>> listCommentsWithFilter(long page, long size, CommentsQueryDTO queryDTO);

    Mono<PageDTO<Comments>> listAICommentsWithFilter(long page, long size, CommentsQueryDTO queryDTO);

    Mono<PageDTO<Comments>> listCommentsByUserId(long page, long size, Long userId);

    Mono<PageDTO<Comments>> listCommentsByArticleId(long page, long size, Long articleId, String sortWay);

    Flux<Comments> listAICommentsByArticleId(Long articleId);

    Mono<Comments> save(Comments comments);

    Mono<Comments> update(Comments comments);

    Mono<Comments> getById(Long id);

    /**
     * 批量查询评论，供内部服务按主键精确同步
     */
    Flux<Comments> listByIds(java.util.Collection<Long> ids);

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
    Mono<List<CommentSyncVO>> getNeo4jSyncComments(String updatedAfter);
}

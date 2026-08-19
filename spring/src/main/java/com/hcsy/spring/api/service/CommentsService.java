package com.hcsy.spring.api.service;

import java.util.List;

import com.hcsy.spring.entity.dto.CommentsQueryDTO;
import com.hcsy.spring.entity.dto.PageDTO;
import com.hcsy.spring.entity.po.Comments;

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
    Mono<java.util.Map<Long, java.util.Map<String, com.hcsy.spring.entity.dto.CommentScoreDTO>>> getCommentScoresByArticleIds(
        java.util.Collection<Long> articleIds);
}

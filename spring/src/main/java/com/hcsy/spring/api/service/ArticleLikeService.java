package com.hcsy.spring.api.service;

import com.hcsy.spring.entity.dto.PageDTO;
import com.hcsy.spring.entity.vo.ArticleLikeVO;

import reactor.core.publisher.Mono;

public interface ArticleLikeService {
    Mono<Boolean> addLike(Long articleId, Long userId);

    Mono<Boolean> removeLike(Long articleId, Long userId);

    Mono<Boolean> isLiked(Long articleId, Long userId);

    Mono<PageDTO<ArticleLikeVO>> listUserLikes(Long userId, long page, long size);

    Mono<Long> getLikeCountByArticleId(Long articleId);
}

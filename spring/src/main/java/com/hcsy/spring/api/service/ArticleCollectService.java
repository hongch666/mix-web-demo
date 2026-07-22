package com.hcsy.spring.api.service;

import com.hcsy.spring.entity.dto.PageDTO;
import com.hcsy.spring.entity.vo.ArticleCollectVO;

import reactor.core.publisher.Mono;

public interface ArticleCollectService {
    Mono<Boolean> addCollect(Long articleId, Long userId);

    Mono<Boolean> removeCollect(Long articleId, Long userId);

    Mono<Boolean> isCollected(Long articleId, Long userId);

    Mono<PageDTO<ArticleCollectVO>> listUserCollects(Long userId, long page, long size);

    Mono<Long> getCollectCountByArticleId(Long articleId);
}

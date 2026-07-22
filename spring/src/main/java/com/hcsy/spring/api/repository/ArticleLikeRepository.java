package com.hcsy.spring.api.repository;

import org.springframework.data.domain.Pageable;
import org.springframework.data.repository.reactive.ReactiveCrudRepository;

import com.hcsy.spring.entity.po.ArticleLike;

import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

public interface ArticleLikeRepository extends ReactiveCrudRepository<ArticleLike, Long> {
    Mono<Boolean> existsByArticleIdAndUserId(Long articleId, Long userId);

    Mono<Void> deleteByArticleIdAndUserId(Long articleId, Long userId);

    Flux<ArticleLike> findByUserIdOrderByCreatedTimeDesc(Long userId, Pageable pageable);

    Mono<Long> countByUserId(Long userId);

    Mono<Long> countByArticleId(Long articleId);
}

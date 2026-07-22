package com.hcsy.spring.api.repository;

import org.springframework.data.domain.Pageable;
import org.springframework.data.repository.reactive.ReactiveCrudRepository;

import com.hcsy.spring.entity.po.Comments;

import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

public interface CommentsRepository extends ReactiveCrudRepository<Comments, Long> {
    Flux<Comments> findByUserIdOrderByCreateTimeDesc(Long userId, Pageable pageable);

    Mono<Long> countByUserId(Long userId);

    Flux<Comments> findByArticleIdOrderByCreateTimeDesc(Long articleId);
}

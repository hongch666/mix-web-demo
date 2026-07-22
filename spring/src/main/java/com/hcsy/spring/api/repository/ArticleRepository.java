package com.hcsy.spring.api.repository;

import org.springframework.data.domain.Pageable;
import org.springframework.data.r2dbc.repository.Modifying;
import org.springframework.data.r2dbc.repository.Query;
import org.springframework.data.repository.reactive.ReactiveCrudRepository;
import org.springframework.data.repository.query.Param;

import com.hcsy.spring.entity.po.Article;

import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

public interface ArticleRepository extends ReactiveCrudRepository<Article, Long> {
    Flux<Article> findByStatusOrderByCreateAtAsc(Integer status);

    Flux<Article> findByStatusOrderByCreateAtAsc(Integer status, Pageable pageable);

    Mono<Long> countByStatus(Integer status);

    Flux<Article> findByUserIdOrderByCreateAtAsc(Long userId, Pageable pageable);

    Mono<Long> countByUserId(Long userId);

    Flux<Article> findByUserIdAndStatusOrderByCreateAtAsc(Long userId, Integer status, Pageable pageable);

    Mono<Long> countByUserIdAndStatus(Long userId, Integer status);

    Mono<Article> findFirstByTitle(String title);

    Flux<Article> findByTitleContaining(String title);

    @Modifying
    @Query("UPDATE articles SET status = 1 WHERE id = :id")
    Mono<Integer> publishById(@Param("id") Long id);

    @Modifying
    @Query("UPDATE articles SET views = views + 1, update_at = update_at WHERE id = :id AND status = 1")
    Mono<Integer> incrementViews(@Param("id") Long id);
}

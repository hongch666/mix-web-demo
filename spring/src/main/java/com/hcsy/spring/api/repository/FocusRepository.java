package com.hcsy.spring.api.repository;

import org.springframework.data.domain.Pageable;
import org.springframework.data.repository.reactive.ReactiveCrudRepository;

import com.hcsy.spring.entity.po.Focus;

import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

public interface FocusRepository extends ReactiveCrudRepository<Focus, Long> {
    Mono<Boolean> existsByUserIdAndFocusId(Long userId, Long focusId);

    Mono<Void> deleteByUserIdAndFocusId(Long userId, Long focusId);

    Flux<Focus> findByUserIdOrderByCreatedTimeDesc(Long userId, Pageable pageable);

    Flux<Focus> findByFocusIdOrderByCreatedTimeDesc(Long focusId, Pageable pageable);

    Mono<Long> countByUserId(Long userId);

    Mono<Long> countByFocusId(Long focusId);
}

package com.hcsy.spring.api.repository;

import org.springframework.data.repository.reactive.ReactiveCrudRepository;

import com.hcsy.spring.entity.po.SubCategory;

import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

public interface SubCategoryRepository extends ReactiveCrudRepository<SubCategory, Long> {
    Flux<SubCategory> findByCategoryIdOrderByIdAsc(Long categoryId);

    Mono<Void> deleteByCategoryId(Long categoryId);
}

package com.hcsy.spring.api.repository;

import org.springframework.data.repository.reactive.ReactiveCrudRepository;

import com.hcsy.spring.entity.po.CategoryReference;

import reactor.core.publisher.Mono;

public interface CategoryReferenceRepository extends ReactiveCrudRepository<CategoryReference, Long> {
    Mono<CategoryReference> findBySubCategoryId(Long subCategoryId);

    Mono<Void> deleteBySubCategoryId(Long subCategoryId);
}

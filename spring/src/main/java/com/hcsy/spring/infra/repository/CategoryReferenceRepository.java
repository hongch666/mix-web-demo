package com.hcsy.spring.infra.repository;

import org.springframework.data.repository.reactive.ReactiveCrudRepository;

import com.hcsy.spring.entity.po.CategoryReference;

import reactor.core.publisher.Mono;

/**
 * 负责子分类引用记录（CategoryReference）的响应式数据访问
 */
public interface CategoryReferenceRepository extends ReactiveCrudRepository<CategoryReference, Long> {
    /**
     * 查询指定子分类的分类引用记录
     */
    Mono<CategoryReference> findBySubCategoryId(Long subCategoryId);

    /**
     * 删除指定子分类的分类引用记录
     */
    Mono<Void> deleteBySubCategoryId(Long subCategoryId);
}

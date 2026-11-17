package com.hcsy.spring.infra.repository;

import org.springframework.data.r2dbc.repository.Query;
import org.springframework.data.repository.reactive.ReactiveCrudRepository;

import com.hcsy.spring.entity.po.CategoryReference;

import reactor.core.publisher.Flux;
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

    /**
     * 查询含 PDF 或链接的权威参考记录，供 OSS 清理任务判断在用引用
     */
    @Query("SELECT * FROM category_reference WHERE pdf IS NOT NULL OR link IS NOT NULL")
    Flux<CategoryReference> findAllWithPdfOrLink();
}

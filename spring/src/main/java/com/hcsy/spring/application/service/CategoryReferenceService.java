package com.hcsy.spring.application.service;

import com.hcsy.spring.entity.dto.CategoryReferenceCreateDTO;
import com.hcsy.spring.entity.dto.CategoryReferenceUpdateDTO;
import com.hcsy.spring.entity.vo.CategoryReferenceVO;

import reactor.core.publisher.Mono;

/**
 * 子分类权威参考资料业务接口，定义参考资料的创建、更新、删除与按子分类查询操作
 */
public interface CategoryReferenceService {
    /**
     * 为子分类新增参考资料，已存在时抛出冲突异常
     */
    Mono<Long> addCategoryReference(CategoryReferenceCreateDTO dto);

    /**
     * 更新子分类的参考资料内容
     */
    Mono<Void> updateCategoryReference(CategoryReferenceUpdateDTO dto);

    /**
     * 按子分类ID删除其参考资料
     */
    Mono<Void> deleteCategoryReference(Long subCategoryId);

    /**
     * 按子分类ID查询参考资料视图对象
     */
    Mono<CategoryReferenceVO> getCategoryReferenceBySubCategoryId(Long subCategoryId);
}

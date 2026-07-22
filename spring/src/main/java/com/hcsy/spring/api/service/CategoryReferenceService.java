package com.hcsy.spring.api.service;

import com.hcsy.spring.entity.dto.CategoryReferenceCreateDTO;
import com.hcsy.spring.entity.dto.CategoryReferenceUpdateDTO;
import com.hcsy.spring.entity.vo.CategoryReferenceVO;

import reactor.core.publisher.Mono;

public interface CategoryReferenceService {
    Mono<Long> addCategoryReference(CategoryReferenceCreateDTO dto);

    Mono<Void> updateCategoryReference(CategoryReferenceUpdateDTO dto);

    Mono<Void> deleteCategoryReference(Long subCategoryId);

    Mono<CategoryReferenceVO> getCategoryReferenceBySubCategoryId(Long subCategoryId);
}

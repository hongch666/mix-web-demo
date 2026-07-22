package com.hcsy.spring.api.service;

import java.util.Collection;
import java.util.List;

import com.hcsy.spring.entity.dto.CategoryCreateDTO;
import com.hcsy.spring.entity.dto.CategoryUpdateDTO;
import com.hcsy.spring.entity.dto.PageDTO;
import com.hcsy.spring.entity.dto.SubCategoryCreateDTO;
import com.hcsy.spring.entity.dto.SubCategoryUpdateDTO;
import com.hcsy.spring.entity.po.Category;
import com.hcsy.spring.entity.vo.CategoryVO;

import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

public interface CategoryService {
    Mono<Long> addCategory(CategoryCreateDTO dto);

    Mono<Void> updateCategory(CategoryUpdateDTO dto);

    Mono<Void> deleteCategory(Long id);

    Mono<Void> deleteCategories(List<Long> ids);

    Mono<Long> addSubCategory(SubCategoryCreateDTO dto);

    Mono<Void> updateSubCategory(SubCategoryUpdateDTO dto);

    Mono<Void> deleteSubCategory(Long id);

    Mono<Void> deleteSubCategories(List<Long> ids);

    Mono<CategoryVO> getCategoryById(Long id);

    Mono<PageDTO<CategoryVO>> pageCategory(long page, long size);

    Flux<Category> listByIds(Collection<Long> ids);
}

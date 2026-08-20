package com.hcsy.spring.api.service;

import java.util.Collection;
import java.util.List;

import com.hcsy.spring.entity.dto.CategoryCreateDTO;
import com.hcsy.spring.entity.dto.CategoryUpdateDTO;
import com.hcsy.spring.entity.dto.PageDTO;
import com.hcsy.spring.entity.dto.SubCategoryCreateDTO;
import com.hcsy.spring.entity.dto.SubCategoryUpdateDTO;
import com.hcsy.spring.entity.po.Category;
import com.hcsy.spring.entity.po.SubCategory;
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

    Flux<SubCategory> listSubCategoriesByIds(Collection<Long> ids);

    // 新增：供内部接口使用的方法
    Flux<Category> listAllCategories();

    Flux<java.util.Map<String, Object>> listAllSubCategoriesWithParent();

    /**
     * 获取分类数据，用于Neo4j同步
     *
     * @param updatedAfter
     *                         增量同步时间（ISO格式），为空则全量
     */
    Mono<List<java.util.Map<String, Object>>> getNeo4jSyncCategories(String updatedAfter);

    /**
     * 获取子分类数据，用于Neo4j同步
     *
     * @param updatedAfter
     *                         增量同步时间（ISO格式），为空则全量
     */
    Mono<List<java.util.Map<String, Object>>> getNeo4jSyncSubCategories(String updatedAfter);
}

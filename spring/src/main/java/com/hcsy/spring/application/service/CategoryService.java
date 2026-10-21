package com.hcsy.spring.application.service;

import java.util.Collection;
import java.util.List;

import com.hcsy.spring.entity.dto.CategoryCreateDTO;
import com.hcsy.spring.entity.dto.CategoryUpdateDTO;
import com.hcsy.spring.entity.dto.PageDTO;
import com.hcsy.spring.entity.dto.SubCategoryCreateDTO;
import com.hcsy.spring.entity.dto.SubCategoryUpdateDTO;
import com.hcsy.spring.entity.po.Category;
import com.hcsy.spring.entity.po.SubCategory;
import com.hcsy.spring.entity.vo.CategorySyncVO;
import com.hcsy.spring.entity.vo.CategoryVO;
import com.hcsy.spring.entity.vo.SubCategorySyncVO;
import com.hcsy.spring.entity.vo.SubCategoryWithParentVO;

import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

/**
 * 分类业务接口，定义分类与子分类的增删改查、多级缓存分页查询及Neo4j同步数据获取等响应式操作
 */
public interface CategoryService {
    /**
     * 新增分类并清除分类相关缓存
     */
    Mono<Long> addCategory(CategoryCreateDTO dto);

    /**
     * 更新分类名称，分类不存在时抛出404异常
     */
    Mono<Void> updateCategory(CategoryUpdateDTO dto);

    /**
     * 删除分类并级联删除其子分类，同时清除分类缓存
     */
    Mono<Void> deleteCategory(Long id);

    /**
     * 批量删除分类并级联删除各自子分类
     */
    Mono<Void> deleteCategories(List<Long> ids);

    /**
     * 在指定分类下新增子分类并清除分类缓存
     */
    Mono<Long> addSubCategory(SubCategoryCreateDTO dto);

    /**
     * 更新子分类名称与所属分类
     */
    Mono<Void> updateSubCategory(SubCategoryUpdateDTO dto);

    /**
     * 删除指定子分类并清除分类缓存
     */
    Mono<Void> deleteSubCategory(Long id);

    /**
     * 批量删除子分类，任一ID不存在时抛出404异常
     */
    Mono<Void> deleteSubCategories(List<Long> ids);

    /**
     * 查询分类详情含子分类列表，走多级缓存
     */
    Mono<CategoryVO> getCategoryById(Long id);

    /**
     * 分页查询分类详情列表，走多级缓存
     */
    Mono<PageDTO<CategoryVO>> pageCategory(long page, long size);

    /**
     * 按ID批量流式查询分类
     */
    Flux<Category> listByIds(Collection<Long> ids);

    /**
     * 按ID批量流式查询子分类
     */
    Flux<SubCategory> listSubCategoriesByIds(Collection<Long> ids);

    // 新增：供内部接口使用的方法
    Flux<Category> listAllCategories();

    /**
     * 查询所有子分类并批量关联其父分类名称，用于内部接口
     */
    Flux<SubCategoryWithParentVO> listAllSubCategoriesWithParent();

    /**
     * 获取分类数据，用于Neo4j同步
     *
     * @param updatedAfter
     *                         增量同步时间（ISO格式），为空则全量
     */
    Mono<List<CategorySyncVO>> getNeo4jSyncCategories(String updatedAfter);

    /**
     * 获取子分类数据，用于Neo4j同步
     *
     * @param updatedAfter
     *                         增量同步时间（ISO格式），为空则全量
     */
    Mono<List<SubCategorySyncVO>> getNeo4jSyncSubCategories(String updatedAfter);
}

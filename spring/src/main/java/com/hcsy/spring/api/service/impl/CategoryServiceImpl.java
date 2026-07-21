package com.hcsy.spring.api.service.impl;

import java.util.List;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.hcsy.spring.api.mapper.CategoryMapper;
import com.hcsy.spring.api.mapper.SubCategoryMapper;
import com.hcsy.spring.api.service.CategoryCacheService;
import com.hcsy.spring.api.service.CategoryService;
import com.hcsy.spring.common.exceptions.BusinessException;
import com.hcsy.spring.common.constants.Messages;
import com.hcsy.spring.common.constants.HttpCode;
import com.hcsy.spring.entity.dto.CategoryCreateDTO;
import com.hcsy.spring.entity.dto.CategoryUpdateDTO;
import com.hcsy.spring.entity.dto.PageDTO;
import com.hcsy.spring.entity.dto.SubCategoryCreateDTO;
import com.hcsy.spring.entity.dto.SubCategoryUpdateDTO;
import com.hcsy.spring.entity.po.Category;
import com.hcsy.spring.entity.po.SubCategory;
import com.hcsy.spring.entity.vo.CategoryVO;

import lombok.RequiredArgsConstructor;

@Service
@RequiredArgsConstructor
public class CategoryServiceImpl extends ServiceImpl<CategoryMapper, Category> implements CategoryService {
    private final CategoryMapper categoryMapper;
    private final SubCategoryMapper subCategoryMapper;
    private final CategoryCacheService categoryCacheService;

    @Override
    @Transactional
    public Long addCategory(CategoryCreateDTO dto) {
        Category category = new Category();
        category.setName(dto.getName());
        categoryMapper.insert(category);
        // 新增分类后清除所有分类缓存
        categoryCacheService.evictAllCategoryCaches();
        return category.getId();
    }

    @Override
    @Transactional
    public void updateCategory(CategoryUpdateDTO dto) {
        Category category = categoryMapper.selectById(dto.getId());
        if (category != null) {
            category.setName(dto.getName());
            categoryMapper.updateById(category);
        }
        // 修改分类后清除指定ID缓存 + 所有分页缓存
        categoryCacheService.evictCategoryByIdCache(dto.getId());
        categoryCacheService.evictAllCategoryCaches();
    }

    @Override
    @Transactional
    public void deleteCategory(Long id) {
        Category existing = categoryMapper.selectById(id);
        if (existing == null) {
            throw BusinessException.builder().httpStatus(HttpCode.NOT_FOUND).errorMessage(Messages.UNDEFINED_CATEGORY).build();
        }
        // 先删子分类
        subCategoryMapper.delete(new QueryWrapper<SubCategory>().eq("category_id", id));
        categoryMapper.deleteById(id);
        // 删除分类后清除指定ID缓存 + 所有分页缓存
        categoryCacheService.evictCategoryByIdCache(id);
        categoryCacheService.evictAllCategoryCaches();
    }

    @Override
    @Transactional
    public void deleteCategories(List<Long> ids) {
        if (ids == null || ids.isEmpty()) {
            return;
        }

        List<Long> distinctIds = ids.stream()
                .filter(id -> id != null)
                .distinct()
                .toList();
        if (distinctIds.isEmpty()) {
            return;
        }

        // 批量删除前校验：必须全部存在（只要有一个不存在就抛异常）
        if (categoryMapper.selectBatchIds(distinctIds).size() != distinctIds.size()) {
            throw BusinessException.builder().httpStatus(HttpCode.NOT_FOUND).errorMessage(Messages.UNDEFINED_CATEGORIES).build();
        }

        for (Long id : ids) {
            deleteCategory(id);
        }
        // 批量删除后清除所有分类缓存
        categoryCacheService.evictAllCategoryCaches();
    }

    @Override
    @Transactional
    public Long addSubCategory(SubCategoryCreateDTO dto) {
        SubCategory sub = new SubCategory();
        sub.setName(dto.getName());
        sub.setCategoryId(dto.getCategoryId());
        subCategoryMapper.insert(sub);
        // 新增子分类后清除父分类缓存 + 所有分页缓存
        categoryCacheService.evictCategoryByIdCache(dto.getCategoryId());
        categoryCacheService.evictAllCategoryCaches();
        return sub.getId();
    }

    @Override
    @Transactional
    public void updateSubCategory(SubCategoryUpdateDTO dto) {
        SubCategory sub = subCategoryMapper.selectById(dto.getId());
        if (sub != null) {
            sub.setName(dto.getName());
            sub.setCategoryId(dto.getCategoryId());
            subCategoryMapper.updateById(sub);
        }
        // 修改子分类后清除父分类缓存 + 所有分页缓存
        if (dto.getCategoryId() != null) {
            categoryCacheService.evictCategoryByIdCache(dto.getCategoryId());
        }
        categoryCacheService.evictAllCategoryCaches();
    }

    @Override
    @Transactional
    public void deleteSubCategory(Long id) {
        SubCategory existing = subCategoryMapper.selectById(id);
        if (existing == null) {
            throw BusinessException.builder().httpStatus(HttpCode.NOT_FOUND).errorMessage(Messages.UNDEFINED_SUB_CATEGORY).build();
        }
        Long categoryId = existing.getCategoryId();
        subCategoryMapper.deleteById(id);
        // 删除子分类后清除父分类缓存 + 所有分页缓存
        if (categoryId != null) {
            categoryCacheService.evictCategoryByIdCache(categoryId);
        }
        categoryCacheService.evictAllCategoryCaches();
    }

    @Override
    @Transactional
    public void deleteSubCategories(List<Long> ids) {
        if (ids == null || ids.isEmpty()) {
            return;
        }
        List<Long> distinctIds = ids.stream()
                .filter(id -> id != null)
                .distinct()
                .toList();
        if (distinctIds.isEmpty()) {
            return;
        }

        // 批量删除前校验：必须全部存在（只要有一个不存在就抛异常）
        if (subCategoryMapper.selectBatchIds(distinctIds).size() != distinctIds.size()) {
            throw BusinessException.builder().httpStatus(HttpCode.NOT_FOUND).errorMessage(Messages.UNDEFINED_SUB_CATEGORIES).build();
        }

        subCategoryMapper.deleteBatchIds(ids);
        // 批量删除子分类后清除所有分类缓存
        categoryCacheService.evictAllCategoryCaches();
    }

    @Transactional(readOnly = true)
    @Override
    public CategoryVO getCategoryById(Long id) {
        return categoryCacheService.getCategoryById(id);
    }

    @Transactional(readOnly = true)
    @Override
    public IPage<CategoryVO> pageCategory(Page<?> page) {
        PageDTO<CategoryVO> dto = categoryCacheService.cachedPageCategory(page);
        IPage<CategoryVO> voPage = new Page<>(dto.getCurrent(), dto.getSize(), dto.getTotal());
        voPage.setRecords(dto.getRecords());
        return voPage;
    }
}

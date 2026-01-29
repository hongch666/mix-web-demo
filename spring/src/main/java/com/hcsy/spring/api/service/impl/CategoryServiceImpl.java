package com.hcsy.spring.api.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.hcsy.spring.api.mapper.CategoryMapper;
import com.hcsy.spring.api.mapper.SubCategoryMapper;
import com.hcsy.spring.api.service.CategoryService;
import com.hcsy.spring.api.service.CategoryCacheService;
import com.hcsy.spring.entity.dto.CategoryCreateDTO;
import com.hcsy.spring.entity.dto.CategoryUpdateDTO;
import com.hcsy.spring.entity.dto.PageDTO;
import com.hcsy.spring.entity.dto.SubCategoryCreateDTO;
import com.hcsy.spring.entity.dto.SubCategoryUpdateDTO;
import com.hcsy.spring.entity.po.Category;
import com.hcsy.spring.entity.po.SubCategory;
import com.hcsy.spring.entity.vo.CategoryVO;
import com.hcsy.spring.common.exceptions.BusinessException;
import com.hcsy.spring.common.utils.Constants;

import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.cache.annotation.CacheConfig;
import org.springframework.cache.annotation.CacheEvict;
import org.springframework.cache.annotation.Caching;

import java.util.List;

@Service
@RequiredArgsConstructor
@CacheConfig(cacheNames = "category")
public class CategoryServiceImpl extends ServiceImpl<CategoryMapper, Category> implements CategoryService {
    private final CategoryMapper categoryMapper;
    private final SubCategoryMapper subCategoryMapper;
    private final CategoryCacheService categoryCacheService;

    @Override
    @Transactional
    @Caching(evict = {
            @CacheEvict(value = "categoryPage", allEntries = true)
    })
    public Long addCategory(CategoryCreateDTO dto) {
        Category category = new Category();
        category.setName(dto.getName());
        categoryMapper.insert(category);
        return category.getId();
    }

    @Override
    @Transactional
    @Caching(evict = {
            @CacheEvict(value = "categoryPage", allEntries = true),
            @CacheEvict(value = "categoryById", key = "#dto.id")
    })
    public void updateCategory(CategoryUpdateDTO dto) {
        Category category = categoryMapper.selectById(dto.getId());
        if (category != null) {
            category.setName(dto.getName());
            categoryMapper.updateById(category);
        }
    }

    @Override
    @Transactional
    @Caching(evict = {
            @CacheEvict(value = "categoryPage", allEntries = true),
            @CacheEvict(value = "categoryById", allEntries = true)
    })
    public void deleteCategory(Long id) {
        Category existing = categoryMapper.selectById(id);
        if (existing == null) {
            throw new BusinessException(Constants.UNDEFINED_CATEGORY);
        }
        // 先删子分类
        subCategoryMapper.delete(new QueryWrapper<SubCategory>().eq("category_id", id));
        categoryMapper.deleteById(id);
    }

    @Override
    @Transactional
    @Caching(evict = {
            @CacheEvict(value = "categoryPage", allEntries = true),
            @CacheEvict(value = "categoryById", allEntries = true)
    })
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
            throw new BusinessException(Constants.UNDEFINED_CATEGORIES);
        }

        // 不通过Mapper的删除, 通过service的删除, 可以批量删除分类对应的子分类
        for (Long id : ids) {
            deleteCategory(id);
        }
    }

    @Override
    @Transactional
    @Caching(evict = {
            @CacheEvict(value = "categoryPage", allEntries = true),
            @CacheEvict(value = "categoryById", key = "#dto.categoryId")
    })
    public Long addSubCategory(SubCategoryCreateDTO dto) {
        SubCategory sub = new SubCategory();
        sub.setName(dto.getName());
        sub.setCategoryId(dto.getCategoryId());
        subCategoryMapper.insert(sub);
        return sub.getId();
    }

    @Override
    @Transactional
    @Caching(evict = {
            @CacheEvict(value = "categoryPage", allEntries = true),
            @CacheEvict(value = "categoryById", key = "#dto.categoryId")
    })
    public void updateSubCategory(SubCategoryUpdateDTO dto) {
        SubCategory sub = subCategoryMapper.selectById(dto.getId());
        if (sub != null) {
            sub.setName(dto.getName());
            sub.setCategoryId(dto.getCategoryId());
            subCategoryMapper.updateById(sub);
        }
    }

    @Override
    @Transactional
    @Caching(evict = {
            @CacheEvict(value = "categoryPage", allEntries = true),
            @CacheEvict(value = "categoryById", allEntries = true)
    })
    public void deleteSubCategory(Long id) {
        SubCategory existing = subCategoryMapper.selectById(id);
        if (existing == null) {
            throw new BusinessException(Constants.UNDEFINED_SUB_CATEGORY);
        }
        subCategoryMapper.deleteById(id);
    }

    @Override
    @Transactional
    @Caching(evict = {
            @CacheEvict(value = "categoryPage", allEntries = true),
            @CacheEvict(value = "categoryById", allEntries = true)
    })
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
            throw new BusinessException(Constants.UNDEFINED_SUB_CATEGORIES);
        }

        subCategoryMapper.deleteBatchIds(ids);
    }

    @Override
    public CategoryVO getCategoryById(Long id) {
        return categoryCacheService.getCategoryById(id);
    }

    @Override
    public IPage<CategoryVO> pageCategory(Page<?> page) {
        // 使用被缓存的 DTO 方法获取分页数据，然后转换为 IPage 返回，保持接口字段不变
        PageDTO<CategoryVO> dto = categoryCacheService.cachedPageCategory(page);
        IPage<CategoryVO> voPage = new Page<>(dto.getCurrent(), dto.getSize(), dto.getTotal());
        voPage.setRecords(dto.getRecords());
        return voPage;
    }
}

package com.hcsy.spring.api.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.hcsy.spring.api.mapper.CategoryMapper;
import com.hcsy.spring.api.mapper.SubCategoryMapper;
import com.hcsy.spring.api.service.CategoryService;
import com.hcsy.spring.entity.dto.CategoryCreateDTO;
import com.hcsy.spring.entity.dto.CategoryUpdateDTO;
import com.hcsy.spring.entity.dto.SubCategoryCreateDTO;
import com.hcsy.spring.entity.dto.SubCategoryUpdateDTO;
import com.hcsy.spring.entity.po.Category;
import com.hcsy.spring.entity.po.SubCategory;
import com.hcsy.spring.entity.vo.CategoryVO;
import com.hcsy.spring.entity.vo.SubCategoryVO;

import lombok.RequiredArgsConstructor;
import org.springframework.beans.BeanUtils;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class CategoryServiceImpl extends ServiceImpl<CategoryMapper, Category> implements CategoryService {
    private final CategoryMapper categoryMapper;
    private final SubCategoryMapper subCategoryMapper;

    @Override
    @Transactional
    public Long addCategory(CategoryCreateDTO dto) {
        Category category = new Category();
        category.setName(dto.getName());
        categoryMapper.insert(category);
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
    }

    @Override
    @Transactional
    public void deleteCategory(Long id) {
        // 先删子分类
        subCategoryMapper.delete(new QueryWrapper<SubCategory>().eq("category_id", id));
        categoryMapper.deleteById(id);
    }

    @Override
    @Transactional
    public void deleteCategories(List<Long> ids) {
        for (Long id : ids) {
            deleteCategory(id);
        }
    }

    @Override
    @Transactional
    public Long addSubCategory(SubCategoryCreateDTO dto) {
        SubCategory sub = new SubCategory();
        sub.setName(dto.getName());
        sub.setCategoryId(dto.getCategoryId());
        subCategoryMapper.insert(sub);
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
    }

    @Override
    @Transactional
    public void deleteSubCategory(Long id) {
        subCategoryMapper.deleteById(id);
    }

    @Override
    public CategoryVO getCategoryById(Long id) {
        Category category = categoryMapper.selectById(id);
        if (category == null)
            return null;
        CategoryVO vo = new CategoryVO();
        BeanUtils.copyProperties(category, vo);
        List<SubCategory> subList = subCategoryMapper.selectList(new QueryWrapper<SubCategory>().eq("category_id", id));
        List<SubCategoryVO> subVOList = subList.stream().map(sub -> {
            SubCategoryVO subVO = new SubCategoryVO();
            BeanUtils.copyProperties(sub, subVO);
            return subVO;
        }).collect(Collectors.toList());
        vo.setSubCategories(subVOList);
        return vo;
    }

    @Override
    public List<CategoryVO> listByIds(List<Long> ids) {
        if (ids == null || ids.isEmpty()) {
            return new ArrayList<>();
        }

        // 批量查询分类
        List<Category> categories = categoryMapper.selectBatchIds(ids);
        if (categories.isEmpty()) {
            return new ArrayList<>();
        }

        // 批量查询这些分类下的所有子分类
        List<SubCategory> allSubCategories = subCategoryMapper.selectList(
                new QueryWrapper<SubCategory>().in("category_id", ids));

        // 按分类ID分组子分类
        java.util.Map<Long, List<SubCategory>> subCategoryMap = allSubCategories.stream()
                .collect(Collectors.groupingBy(SubCategory::getCategoryId));

        // 组装结果
        return categories.stream().map(category -> {
            CategoryVO vo = new CategoryVO();
            BeanUtils.copyProperties(category, vo);

            List<SubCategory> subList = subCategoryMap.getOrDefault(category.getId(), new ArrayList<>());
            List<SubCategoryVO> subVOList = subList.stream().map(sub -> {
                SubCategoryVO subVO = new SubCategoryVO();
                BeanUtils.copyProperties(sub, subVO);
                return subVO;
            }).collect(Collectors.toList());

            vo.setSubCategories(subVOList);
            return vo;
        }).collect(Collectors.toList());
    }

    @Override
    public List<Object> getCategoriesById(List<Long> ids) {
        if (ids == null || ids.isEmpty()) {
            return new ArrayList<>();
        }

        // 批量查询分类
        List<Category> categories = categoryMapper.selectBatchIds(ids);
        return new ArrayList<>(categories);
    }

    @Override
    public List<Object> getSubCategoriesByIds(List<Long> subCategoryIds) {
        if (subCategoryIds == null || subCategoryIds.isEmpty()) {
            return new ArrayList<>();
        }

        // 根据子分类ID批量查询子分类
        List<SubCategory> subCategories = subCategoryMapper.selectBatchIds(subCategoryIds);
        return new ArrayList<>(subCategories);
    }

    @Override
    public List<Object> getSubCategoriesByCategoryIds(List<Long> categoryIds) {
        if (categoryIds == null || categoryIds.isEmpty()) {
            return new ArrayList<>();
        }

        // 根据分类ID批量查询子分类
        List<SubCategory> subCategories = subCategoryMapper.selectList(
                new QueryWrapper<SubCategory>().in("category_id", categoryIds));
        return new ArrayList<>(subCategories);
    }

    @Override
    public Map<String, Object> getCategoriesAndSubCategoriesById(List<Long> ids) {
        Map<String, Object> result = new HashMap<>();

        if (ids == null || ids.isEmpty()) {
            result.put("categories", new ArrayList<>());
            result.put("subCategories", new ArrayList<>());
            result.put("totalCategories", 0);
            result.put("totalSubCategories", 0);
            return result;
        }

        // 批量查询分类
        List<Category> categories = categoryMapper.selectBatchIds(ids);

        // 批量查询这些分类下的所有子分类
        List<SubCategory> subCategories = subCategoryMapper.selectList(
                new QueryWrapper<SubCategory>().in("category_id", ids));

        result.put("categories", categories);
        result.put("subCategories", subCategories);
        result.put("totalCategories", categories.size());
        result.put("totalSubCategories", subCategories.size());

        return result;
    }

    @Override
    public IPage<CategoryVO> pageCategory(Page<?> page) {
        Page<Category> categoryPage = new Page<>(page.getCurrent(), page.getSize());
        IPage<Category> resultPage = categoryMapper.selectPage(categoryPage, new QueryWrapper<>());
        List<CategoryVO> voList = new ArrayList<>();
        for (Category category : resultPage.getRecords()) {
            CategoryVO vo = getCategoryById(category.getId());
            voList.add(vo);
        }
        IPage<CategoryVO> voPage = new Page<>(page.getCurrent(), page.getSize(), resultPage.getTotal());
        voPage.setRecords(voList);
        return voPage;
    }
}

package com.hcsy.spring.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.hcsy.spring.dto.CategoryCreateDTO;
import com.hcsy.spring.dto.CategoryUpdateDTO;
import com.hcsy.spring.dto.SubCategoryCreateDTO;
import com.hcsy.spring.dto.SubCategoryUpdateDTO;
import com.hcsy.spring.mapper.CategoryMapper;
import com.hcsy.spring.mapper.SubCategoryMapper;
import com.hcsy.spring.po.Category;
import com.hcsy.spring.po.SubCategory;
import com.hcsy.spring.service.CategoryService;
import com.hcsy.spring.vo.CategoryVO;
import com.hcsy.spring.vo.SubCategoryVO;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.BeanUtils;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.ArrayList;
import java.util.List;
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

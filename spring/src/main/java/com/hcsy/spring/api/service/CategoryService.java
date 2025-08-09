package com.hcsy.spring.api.service;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.hcsy.spring.entity.dto.CategoryCreateDTO;
import com.hcsy.spring.entity.dto.CategoryUpdateDTO;
import com.hcsy.spring.entity.dto.SubCategoryCreateDTO;
import com.hcsy.spring.entity.dto.SubCategoryUpdateDTO;
import com.hcsy.spring.entity.vo.CategoryVO;

import java.util.List;
import java.util.Map;

public interface CategoryService {
    Long addCategory(CategoryCreateDTO dto);

    void updateCategory(CategoryUpdateDTO dto);

    void deleteCategory(Long id);

    void deleteCategories(List<Long> ids);

    Long addSubCategory(SubCategoryCreateDTO dto);

    void updateSubCategory(SubCategoryUpdateDTO dto);

    void deleteSubCategory(Long id);

    CategoryVO getCategoryById(Long id);

    List<CategoryVO> listByIds(List<Long> ids);

    List<Object> getCategoriesById(List<Long> ids);

    List<Object> getSubCategoriesByIds(List<Long> subCategoryIds);

    List<Object> getSubCategoriesByCategoryIds(List<Long> categoryIds);

    Map<String, Object> getCategoriesAndSubCategoriesById(List<Long> ids);

    IPage<CategoryVO> pageCategory(Page<?> page);
}

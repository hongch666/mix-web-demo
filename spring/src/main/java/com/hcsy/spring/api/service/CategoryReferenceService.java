package com.hcsy.spring.api.service;

import com.baomidou.mybatisplus.extension.service.IService;
import com.hcsy.spring.entity.dto.CategoryReferenceCreateDTO;
import com.hcsy.spring.entity.dto.CategoryReferenceUpdateDTO;
import com.hcsy.spring.entity.po.CategoryReference;
import com.hcsy.spring.entity.vo.CategoryReferenceVO;

public interface CategoryReferenceService extends IService<CategoryReference> {
    /**
     * 创建权威参考文本
     * 一个子分类只能有一个参考文本，需要进行校验
     */
    Long addCategoryReference(CategoryReferenceCreateDTO dto);

    /**
     * 修改权威参考文本
     * 可以修改type和内容，如果修改type则清空旧type的参数
     */
    void updateCategoryReference(CategoryReferenceUpdateDTO dto);

    /**
     * 根据子分类ID删除权威参考文本
     */
    void deleteCategoryReference(Long subCategoryId);

    /**
     * 根据子分类ID获取权威参考文本
     * 如果不存在返回null
     */
    CategoryReferenceVO getCategoryReferenceBySubCategoryId(Long subCategoryId);
}

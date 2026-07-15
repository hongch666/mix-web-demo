package com.hcsy.spring.api.service.impl;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.hcsy.spring.api.mapper.CategoryReferenceMapper;
import com.hcsy.spring.api.mapper.SubCategoryMapper;
import com.hcsy.spring.api.service.CategoryReferenceService;
import com.hcsy.spring.common.exceptions.BusinessException;
import com.hcsy.spring.common.constants.Messages;
import com.hcsy.spring.common.constants.HttpCode;
import com.hcsy.spring.entity.dto.CategoryReferenceCreateDTO;
import com.hcsy.spring.entity.dto.CategoryReferenceUpdateDTO;
import com.hcsy.spring.entity.po.CategoryReference;
import com.hcsy.spring.entity.po.SubCategory;
import com.hcsy.spring.entity.vo.CategoryReferenceVO;

import cn.hutool.core.bean.BeanUtil;
import lombok.RequiredArgsConstructor;

@Service
@RequiredArgsConstructor
public class CategoryReferenceServiceImpl extends ServiceImpl<CategoryReferenceMapper, CategoryReference>
        implements CategoryReferenceService {

    private final CategoryReferenceMapper categoryReferenceMapper;
    private final SubCategoryMapper subCategoryMapper;

    @Override
    @Transactional
    public Long addCategoryReference(CategoryReferenceCreateDTO dto) {
        // 校验子分类是否存在
        SubCategory subCategory = subCategoryMapper.selectById(dto.getSubCategoryId());
        if (subCategory == null) {
            throw BusinessException.builder().httpStatus(HttpCode.NOT_FOUND).errorMessage(Messages.UNDEFINED_SUB_CATEGORY).build();
        }

        // 校验一个子分类只能有一个参考文本
        CategoryReference existing = categoryReferenceMapper.selectOne(
                new QueryWrapper<CategoryReference>().eq("sub_category_id", dto.getSubCategoryId()));
        if (existing != null) {
            throw BusinessException.builder().httpStatus(HttpCode.CONFLICT).errorMessage(Messages.REFERENCE_EXIST).build();
        }

        // 验证PDF链接后缀
        if ("pdf".equals(dto.getType())) {
            if (dto.getPdf() == null || dto.getPdf().isEmpty()) {
                throw BusinessException.builder().httpStatus(HttpCode.UNPROCESSABLE_ENTITY).errorMessage(Messages.PDF_EMPTY).build();
            }
            if (!dto.getPdf().toLowerCase().endsWith(".pdf")) {
                throw BusinessException.builder().httpStatus(HttpCode.UNPROCESSABLE_ENTITY).errorMessage(Messages.PDF_TAIL).build();
            }
        }

        // 验证link链接
        if ("link".equals(dto.getType())) {
            if (dto.getLink() == null || dto.getLink().isEmpty()) {
                throw BusinessException.builder().httpStatus(HttpCode.UNPROCESSABLE_ENTITY).errorMessage(Messages.LINK_EMPTY).build();
            }
        }

        CategoryReference reference = BeanUtil.copyProperties(dto, CategoryReference.class);

        if ("link".equals(dto.getType())) {
            reference.setLink(dto.getLink());
            reference.setPdf(null);
        } else if ("pdf".equals(dto.getType())) {
            reference.setPdf(dto.getPdf());
            reference.setLink(null);
        }

        categoryReferenceMapper.insert(reference);
        return reference.getId();
    }

    @Override
    @Transactional
    public void updateCategoryReference(CategoryReferenceUpdateDTO dto) {
        // 校验子分类是否存在
        SubCategory subCategory = subCategoryMapper.selectById(dto.getSubCategoryId());
        if (subCategory == null) {
            throw BusinessException.builder().httpStatus(HttpCode.NOT_FOUND).errorMessage(Messages.UNDEFINED_SUB_CATEGORY).build();
        }

        // 根据子分类ID查询参考文本
        CategoryReference reference = categoryReferenceMapper.selectOne(
                new QueryWrapper<CategoryReference>().eq("sub_category_id", dto.getSubCategoryId()));
        if (reference == null) {
            throw BusinessException.builder().httpStatus(HttpCode.CONFLICT).errorMessage(Messages.REFERENCE_EXIST).build();
        }

        // 验证PDF链接后缀
        if ("pdf".equals(dto.getType())) {
            if (dto.getPdf() == null || dto.getPdf().isEmpty()) {
                throw BusinessException.builder().httpStatus(HttpCode.UNPROCESSABLE_ENTITY).errorMessage(Messages.PDF_EMPTY).build();
            }
            if (!dto.getPdf().toLowerCase().endsWith(".pdf")) {
                throw BusinessException.builder().httpStatus(HttpCode.UNPROCESSABLE_ENTITY).errorMessage(Messages.PDF_TAIL).build();
            }
        }

        // 验证link链接
        if ("link".equals(dto.getType())) {
            if (dto.getLink() == null || dto.getLink().isEmpty()) {
                throw BusinessException.builder().httpStatus(HttpCode.UNPROCESSABLE_ENTITY).errorMessage(Messages.LINK_EMPTY).build();
            }
        }

        // 根据DTO的type判断，清除另一个type对应的数据
        reference.setType(dto.getType());

        if ("link".equals(dto.getType())) {
            reference.setLink(dto.getLink());
            reference.setPdf(null);
        } else if ("pdf".equals(dto.getType())) {
            reference.setPdf(dto.getPdf());
            reference.setLink(null);
        }

        categoryReferenceMapper.updateById(reference);
    }

    @Override
    @Transactional
    public void deleteCategoryReference(Long subCategoryId) {
        CategoryReference reference = categoryReferenceMapper.selectOne(
                new QueryWrapper<CategoryReference>().eq("sub_category_id", subCategoryId));
        if (reference != null) {
            categoryReferenceMapper.deleteById(reference.getId());
        } else {
            throw BusinessException.builder().httpStatus(HttpCode.CONFLICT).errorMessage(Messages.REFERENCE_EXIST).build();
        }
    }

    @Override
    public CategoryReferenceVO getCategoryReferenceBySubCategoryId(Long subCategoryId) {
        CategoryReference reference = categoryReferenceMapper.selectOne(
                new QueryWrapper<CategoryReference>().eq("sub_category_id", subCategoryId));

        if (reference == null) {
            return null;
        }

        CategoryReferenceVO vo = new CategoryReferenceVO();
        vo.setId(reference.getId());
        vo.setSubCategoryId(reference.getSubCategoryId());
        vo.setType(reference.getType());

        // 只返回对应type的数据
        if ("link".equals(reference.getType())) {
            vo.setLink(reference.getLink());
            vo.setPdf(null);
        } else if ("pdf".equals(reference.getType())) {
            vo.setPdf(reference.getPdf());
            vo.setLink(null);
        }

        return vo;
    }
}

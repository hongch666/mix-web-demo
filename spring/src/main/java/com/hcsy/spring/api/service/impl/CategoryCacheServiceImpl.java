package com.hcsy.spring.api.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.hcsy.spring.api.mapper.CategoryMapper;
import com.hcsy.spring.api.mapper.SubCategoryMapper;
import com.hcsy.spring.api.service.CategoryCacheService;
import com.hcsy.spring.common.utils.SimpleLogger;
import com.hcsy.spring.entity.dto.PageDTO;
import com.hcsy.spring.entity.po.Category;
import com.hcsy.spring.entity.po.SubCategory;
import com.hcsy.spring.entity.vo.CategoryVO;
import com.hcsy.spring.entity.vo.SubCategoryVO;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.BeanUtils;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.List;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class CategoryCacheServiceImpl implements CategoryCacheService {

    private final CategoryMapper categoryMapper;
    private final SubCategoryMapper subCategoryMapper;
    private final SimpleLogger logger;

    @Override
    @Cacheable(value = "categoryById", key = "#id", unless = "#result == null")
    public CategoryVO getCategoryById(Long id) {
        logger.info("缓存未命中，从数据库加载 category id={}", id);
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
    @Cacheable(value = "categoryPage", key = "T(java.lang.String).format('p_%d_s_%d', #page.current, #page.size)", unless = "#result == null")
    public PageDTO<CategoryVO> cachedPageCategory(Page<?> page) {
        logger.info("缓存未命中，从数据库加载分页数据 page={} size={}", page.getCurrent(), page.getSize());
        Page<Category> categoryPage = new Page<>(page.getCurrent(), page.getSize());
        IPage<Category> resultPage = categoryMapper.selectPage(categoryPage, new QueryWrapper<>());
        List<CategoryVO> voList = new ArrayList<>();
        for (Category category : resultPage.getRecords()) {
            // 这里调用自己的缓存方法，避免重复查询
            CategoryVO vo = getCategoryById(category.getId());
            voList.add(vo);
        }
        PageDTO<CategoryVO> pageDTO = new PageDTO<>();
        pageDTO.setCurrent(resultPage.getCurrent());
        pageDTO.setSize(resultPage.getSize());
        pageDTO.setTotal(resultPage.getTotal());
        pageDTO.setRecords(voList);
        return pageDTO;
    }
}

package com.hcsy.spring.api.service.impl;

import java.util.ArrayList;
import java.util.List;
import java.util.stream.Collectors;

import org.springframework.beans.BeanUtils;
import org.springframework.stereotype.Service;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.hcsy.spring.api.mapper.CategoryMapper;
import com.hcsy.spring.api.mapper.SubCategoryMapper;
import com.hcsy.spring.api.service.CategoryCacheService;
import com.hcsy.spring.common.constants.Messages;
import com.hcsy.spring.common.utils.RedisUtil;
import com.hcsy.spring.common.utils.SimpleLogger;
import com.hcsy.spring.entity.dto.PageDTO;
import com.hcsy.spring.entity.po.Category;
import com.hcsy.spring.entity.po.SubCategory;
import com.hcsy.spring.entity.vo.CategoryVO;
import com.hcsy.spring.entity.vo.SubCategoryVO;

import lombok.RequiredArgsConstructor;

@Service
@RequiredArgsConstructor
public class CategoryCacheServiceImpl implements CategoryCacheService {

    private final CategoryMapper categoryMapper;
    private final SubCategoryMapper subCategoryMapper;
    private final RedisUtil redisUtil;
    private final ObjectMapper objectMapper;
    private final SimpleLogger logger;

    private static final String CATEGORY_BY_ID_KEY = "category:byId:%d";
    private static final String CATEGORY_PAGE_KEY = "category:page:p_%d_s_%d";
    private static final long CACHE_TTL_SECONDS = 24 * 60 * 60L;

    @Override
    public CategoryVO getCategoryById(Long id) {
        String cacheKey = CATEGORY_BY_ID_KEY.formatted(id);
        // 读缓存（阻塞式 API，与 TokenServiceImpl 同样的处理方式）
        try {
            String cached = redisUtil.get(cacheKey);
            if (cached != null && !cached.isEmpty()) {
                return objectMapper.readValue(cached, CategoryVO.class);
            }
        } catch (Exception e) {
            logger.error("分类缓存读取失败: " + e.getMessage());
        }

        // 缓存未命中，从数据库加载
        logger.info(Messages.CATEGORY_CACHE);
        Category category = categoryMapper.selectById(id);
        if (category == null)
            return null;
        CategoryVO vo = buildCategoryVO(category);

        // 写入缓存
        try {
            String json = objectMapper.writeValueAsString(vo);
            redisUtil.set(cacheKey, json, CACHE_TTL_SECONDS);
        } catch (Exception e) {
            logger.error("分类缓存写入失败: " + e.getMessage());
        }

        return vo;
    }

    @Override
    public PageDTO<CategoryVO> cachedPageCategory(Page<?> page) {
        String cacheKey = CATEGORY_PAGE_KEY.formatted(page.getCurrent(), page.getSize());
        // 读缓存
        try {
            String cached = redisUtil.get(cacheKey);
            if (cached != null && !cached.isEmpty()) {
                return objectMapper.readValue(cached, new TypeReference<PageDTO<CategoryVO>>() {});
            }
        } catch (Exception e) {
            logger.error("分类分页缓存读取失败: " + e.getMessage());
        }

        // 缓存未命中，从数据库加载
        logger.info(Messages.CATEGORY_CACHE_PAGE);
        Page<Category> categoryPage = new Page<>(page.getCurrent(), page.getSize());
        IPage<Category> resultPage = categoryMapper.selectPage(categoryPage, new QueryWrapper<>());
        List<CategoryVO> voList = new ArrayList<>();
        for (Category category : resultPage.getRecords()) {
            CategoryVO vo = buildCategoryVO(category);
            voList.add(vo);
        }
        PageDTO<CategoryVO> pageDTO = new PageDTO<>();
        pageDTO.setCurrent(resultPage.getCurrent());
        pageDTO.setSize(resultPage.getSize());
        pageDTO.setTotal(resultPage.getTotal());
        pageDTO.setRecords(voList);

        // 写入缓存
        try {
            String json = objectMapper.writeValueAsString(pageDTO);
            redisUtil.set(cacheKey, json, CACHE_TTL_SECONDS);
        } catch (Exception e) {
            logger.error("分类分页缓存写入失败: " + e.getMessage());
        }

        return pageDTO;
    }

    @Override
    public void evictAllCategoryCaches() {
        // 使用阻塞 API 批量删除
        java.util.Set<String> keys = redisUtil.getKeys("category:*");
        if (keys == null || keys.isEmpty()) {
            return;
        }
        for (String key : keys) {
            try {
                redisUtil.delete(key);
            } catch (Exception e) {
                logger.error("分类缓存清除失败: " + e.getMessage());
            }
        }
    }

    @Override
    public void evictCategoryByIdCache(Long id) {
        String cacheKey = CATEGORY_BY_ID_KEY.formatted(id);
        try {
            redisUtil.delete(cacheKey);
        } catch (Exception e) {
            logger.error("分类缓存清除失败: " + e.getMessage());
        }
    }

    @SuppressWarnings("null")
    private CategoryVO buildCategoryVO(Category category) {
        CategoryVO vo = new CategoryVO();
        BeanUtils.copyProperties(category, vo);
        List<SubCategory> subList = subCategoryMapper.selectList(
                new QueryWrapper<SubCategory>().eq("category_id", category.getId()));
        List<SubCategoryVO> subVOList = subList.stream().map(sub -> {
            SubCategoryVO subVO = new SubCategoryVO();
            BeanUtils.copyProperties(sub, subVO);
            return subVO;
        }).collect(Collectors.toList());
        vo.setSubCategories(subVOList);
        return vo;
    }
}

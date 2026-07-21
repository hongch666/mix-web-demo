package com.hcsy.spring.api.service;

import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.hcsy.spring.entity.dto.PageDTO;
import com.hcsy.spring.entity.vo.CategoryVO;

public interface CategoryCacheService {

    CategoryVO getCategoryById(Long id);

    PageDTO<CategoryVO> cachedPageCategory(Page<?> page);

    /**
     * 清除所有分类相关缓存（分页 + 按ID）
     */
    void evictAllCategoryCaches();

    /**
     * 清除指定 ID 的分类缓存
     */
    void evictCategoryByIdCache(Long id);
}

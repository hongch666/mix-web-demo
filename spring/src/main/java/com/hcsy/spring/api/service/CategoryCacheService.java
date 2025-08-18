package com.hcsy.spring.api.service;

import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.hcsy.spring.entity.dto.PageDTO;
import com.hcsy.spring.entity.vo.CategoryVO;

public interface CategoryCacheService {

    CategoryVO getCategoryById(Long id);

    PageDTO<CategoryVO> cachedPageCategory(Page<?> page);
}

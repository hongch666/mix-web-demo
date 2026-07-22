package com.hcsy.spring.api.service;

import com.hcsy.spring.entity.dto.PageDTO;
import com.hcsy.spring.entity.vo.CategoryVO;

import reactor.core.publisher.Mono;

public interface CategoryCacheService {
    Mono<CategoryVO> getCategoryById(Long id);

    Mono<PageDTO<CategoryVO>> cachedPageCategory(long page, long size);

    Mono<Void> evictAllCategoryCaches();

    Mono<Void> evictCategoryByIdCache(Long id);
}

package com.hcsy.spring.common.cache;

import com.github.benmanes.caffeine.cache.AsyncCache;
import com.hcsy.spring.entity.dto.PageDTO;
import com.hcsy.spring.entity.vo.CategoryVO;

import lombok.Getter;
import lombok.RequiredArgsConstructor;

@Getter
@RequiredArgsConstructor
public class CategoryLocalCache {
    private final AsyncCache<Long, CategoryVO> categoryByIdCache;
    private final AsyncCache<String, PageDTO<CategoryVO>> categoryPageCache;

    public void evictAll() {
        categoryByIdCache.synchronous().invalidateAll();
        categoryPageCache.synchronous().invalidateAll();
    }

    public void evictById(Long id) {
        categoryByIdCache.synchronous().invalidate(id);
        categoryPageCache.synchronous().invalidateAll();
    }
}

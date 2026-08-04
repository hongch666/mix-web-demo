package com.hcsy.spring.common.cache;

import com.github.benmanes.caffeine.cache.AsyncCache;
import com.hcsy.spring.entity.vo.UserListVO;

import lombok.Getter;
import lombok.RequiredArgsConstructor;

@Getter
@RequiredArgsConstructor
public class UserLocalCache {
    private final AsyncCache<String, UserListVO> allUsersCache;

    public void evictAll() {
        allUsersCache.synchronous().invalidateAll();
    }
}

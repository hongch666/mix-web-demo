package com.hcsy.spring.api.service;

import com.hcsy.spring.entity.vo.UserListVO;

import reactor.core.publisher.Mono;

public interface UserCacheService {
    Mono<UserListVO> getAllUsers();

    Mono<Void> evictAllUsersCache();
}

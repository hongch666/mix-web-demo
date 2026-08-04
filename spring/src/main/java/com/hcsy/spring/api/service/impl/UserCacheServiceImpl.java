package com.hcsy.spring.api.service.impl;

import java.util.List;

import org.springframework.stereotype.Service;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.hcsy.spring.api.repository.UserRepository;
import com.hcsy.spring.api.service.UserCacheService;
import com.hcsy.spring.common.cache.CacheInvalidationPublisher;
import com.hcsy.spring.common.cache.ReactiveLocalCache;
import com.hcsy.spring.common.cache.UserLocalCache;
import com.hcsy.spring.common.constants.Messages;
import com.hcsy.spring.common.constants.RedisKeys;
import com.hcsy.spring.common.utils.RedisUtil;
import com.hcsy.spring.common.utils.SimpleLogger;
import com.hcsy.spring.entity.vo.UserListVO;
import com.hcsy.spring.entity.vo.UserVO;

import cn.hutool.core.bean.BeanUtil;
import lombok.RequiredArgsConstructor;
import reactor.core.publisher.Mono;

@Service
@RequiredArgsConstructor
public class UserCacheServiceImpl implements UserCacheService {
    private static final String AI_ROLE = "ai";
    private static final long ALL_USERS_CACHE_TTL_SECONDS = 24 * 60 * 60L;

    private final UserRepository userRepository;
    private final RedisUtil redisUtil;
    private final ObjectMapper objectMapper;
    private final SimpleLogger logger;
    private final UserLocalCache userLocalCache;
    private final ReactiveLocalCache reactiveLocalCache;
    private final CacheInvalidationPublisher cacheInvalidationPublisher;

    @Override
    public Mono<UserListVO> getAllUsers() {
        String cacheKey = RedisKeys.allUsersCache();
        return reactiveLocalCache.get(userLocalCache.getAllUsersCache(), cacheKey,
            () -> loadAllUsersFromRedisOrDatabase(cacheKey));
    }

    private Mono<UserListVO> loadAllUsersFromRedisOrDatabase(String cacheKey) {
        return redisUtil.get(cacheKey)
            .flatMap(json -> Mono.fromCallable(() -> objectMapper.readValue(json, UserListVO.class)))
            .onErrorResume(error -> {
                logger.error(Messages.USER_LIST_CACHE_READ_FAILED, error.getMessage(), error);
                return Mono.empty();
            })
            .switchIfEmpty(Mono.defer(() -> loadAllUsers()
                .flatMap(result -> writeUsersCache(result).thenReturn(result))));
    }

    private Mono<UserListVO> loadAllUsers() {
        return userRepository.findByRoleNotOrderByIdAsc(AI_ROLE)
            .map(user -> BeanUtil.copyProperties(user, UserVO.class))
            .collectList()
            .map(records -> userList(records, records.size()));
    }

    @Override
    public Mono<Void> evictAllUsersCache() {
        return Mono.fromRunnable(userLocalCache::evictAll)
            .then(redisUtil.delete(RedisKeys.allUsersCache()))
            .onErrorResume(error -> {
                logger.error(Messages.USER_LIST_CACHE_EVICT_FAILED, error.getMessage(), error);
                return Mono.just(false);
            })
            .then(cacheInvalidationPublisher.publishUserEviction());
    }

    private Mono<Void> writeUsersCache(UserListVO result) {
        long ttl = result.getTotal() == 0 ? 10 * 60L : ALL_USERS_CACHE_TTL_SECONDS;
        return Mono.fromCallable(() -> objectMapper.writeValueAsString(result))
            .flatMap(json -> redisUtil.set(RedisKeys.allUsersCache(), json, ttl))
            .onErrorResume(error -> {
                logger.error(Messages.USER_LIST_CACHE_WRITE_FAILED, error.getMessage(), error);
                return Mono.just(false);
            })
            .then();
    }

    private UserListVO userList(List<UserVO> users, long total) {
        return UserListVO.builder().total(total).list(users).build();
    }
}

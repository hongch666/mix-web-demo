package com.hcsy.spring.common.utils;

import com.hcsy.spring.common.constants.RedisKeys;

import reactor.core.publisher.Mono;

/**
 * 用户角色缓存
 * 权限校验的热路径按用户 ID 读取角色，缓存定义集中在此，写入方与失效方共用同一份配置
 */
public final class UserRoleCache {

    /** L1 一分钟、L2 五分钟，角色变更后最迟五分钟生效 */
    public static final CacheUtil.CacheOptions<String> OPTIONS = CacheUtil.CacheOptions.fixed(
        RedisKeys.userRoleCacheName(), RedisKeys.userCacheInvalidationChannel(), 1000, 60, 300);

    private UserRoleCache() {
    }

    /**
     * 用户角色变更或用户删除后清理缓存
     */
    public static Mono<Void> evict(CacheUtil cacheUtil, Long userId) {
        return cacheUtil.evict(RedisKeys.userRole(userId), OPTIONS);
    }
}

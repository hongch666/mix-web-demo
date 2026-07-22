package com.hcsy.spring.common.constants;

/**
 * Redis Key 常量类，统一管理所有 Redis Key 的前缀和生成方法
 */
public final class RedisKeys {
    private RedisKeys() {}

    private static final String USER_STATUS_PREFIX = "user:status:";
    private static final String CATEGORY_BY_ID_PREFIX = "category:byId:";

    /**
     * 生成用户登录状态的 Redis Key
     *
     * @param userId 用户ID
     * @return Redis Key
     */
    public static String userStatus(Long userId) {
        return USER_STATUS_PREFIX + userId;
    }

    public static String categoryId(Long categoryId) {
        return CATEGORY_BY_ID_PREFIX + categoryId;
    }
}

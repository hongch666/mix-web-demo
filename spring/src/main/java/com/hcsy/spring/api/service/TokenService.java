package com.hcsy.spring.api.service;

import java.util.List;

/**
 * Token 管理服务接口
 * 负责管理用户的登录 Token，实现多端登录、手动下线等功能
 */
public interface TokenService {
    /**
     * 用户登录时：保存 Token 到 Redis
     */
    void saveToken(Long userId, String token);

    /**
     * 用户登出时：从 Redis 移除 Token
     */
    void removeToken(Long userId, String token);

    /**
     * 验证 Token 是否有效且在 Redis 列表中
     * 
     * @return true 表示 Token 有效且在列表中；false 表示无效或不在列表中
     */
    boolean validateTokenInRedis(Long userId, String token);

    /**
     * 获取用户在线设备数（登录会话数）
     */
    long getUserOnlineDeviceCount(Long userId);

    /**
     * 获取用户所有登录 Token
     */
    List<String> getUserTokens(Long userId);

    /**
     * 手动下线用户：删除该用户的所有 Token
     */
    void forceLogoutUser(Long userId);

    /**
     * 踢出其他设备：清除该用户除 currentToken 外的所有 Token
     *
     * @return 被清除的 Token 数量
     */
    int removeOtherTokens(Long userId, String currentToken);

    /**
     * 定时任务：检查并清理所有过期的 Token
     * 建议每小时执行一次
     */
    void cleanupExpiredTokens();
}

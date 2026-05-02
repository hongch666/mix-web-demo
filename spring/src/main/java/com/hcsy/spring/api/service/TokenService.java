package com.hcsy.spring.api.service;

import java.util.List;

import com.hcsy.spring.entity.vo.TokenRefreshVO;
import com.hcsy.spring.entity.vo.UserLoginVO;

/**
 * Token 管理服务接口
 * 基于 session 的双 token 机制，支持 access/refresh token 的完整生命周期管理
 */
public interface TokenService {

    /**
     * 创建登录会话：生成 access token 和 refresh token，写入 Redis session 体系
     */
    UserLoginVO createLoginSession(Long userId, String username);

    /**
     * 刷新 access token：校验 refresh token，轮换生成新的 access/refresh token
     */
    TokenRefreshVO refreshToken(String refreshToken);

    /**
     * 通过 access token 移除登录会话（登出）
     */
    void removeSessionByAccessToken(String accessToken);

    /**
     * 移除指定用户的指定 session
     */
    void removeSession(Long userId, String sessionId);

    /**
     * 校验 access token 在 Redis 中的有效性
     */
    boolean validateAccessTokenInRedis(Long userId, String sessionId, String accessToken);

    /**
     * 获取用户在线设备数
     */
    long getUserOnlineDeviceCount(Long userId);

    /**
     * 获取用户所有 sessionId 列表
     */
    List<String> getUserSessions(Long userId);

    /**
     * 手动下线用户：删除该用户所有 session
     */
    void forceLogoutUser(Long userId);

    /**
     * 踢出其他设备：保留当前 session，删除其他 session
     */
    int removeOtherSessions(Long userId, String currentAccessToken);

    /**
     * 定时任务：检查并清理所有过期的 session
     */
    void cleanupExpiredTokens();
}

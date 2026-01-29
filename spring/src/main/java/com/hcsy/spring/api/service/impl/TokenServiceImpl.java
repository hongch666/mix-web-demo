package com.hcsy.spring.api.service.impl;

import com.hcsy.spring.api.service.TokenService;
import com.hcsy.spring.common.utils.RedisUtil;
import com.hcsy.spring.common.utils.SimpleLogger;
import com.hcsy.spring.common.utils.Constants;
import com.hcsy.spring.common.utils.JwtUtil;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Set;

/**
 * Token 管理服务实现
 * 负责管理用户的登录 Token，实现多端登录、手动下线等功能
 */
@Service
@RequiredArgsConstructor
public class TokenServiceImpl implements TokenService {
    private final SimpleLogger logger;

    private final RedisUtil redisUtil;
    private final JwtUtil jwtUtil;

    /**
     * 用户登录时：保存 Token 到 Redis
     */
    @Override
    public void saveToken(Long userId, String token) {
        String key = "user:tokens:" + userId;
        // 1. 添加 Token 到列表
        redisUtil.addToList(key, token);
        // 2. 设置列表过期时间（与 Token 有效期一致，如 1 天）
        redisUtil.expire(key, 24 * 60 * 60);
        // 3. 标记用户在线
        redisUtil.set("user:status:" + userId, "1", 24 * 60 * 60);

        logger.info(Constants.LOGIN_TOKEN, userId);
    }

    /**
     * 用户登出时：从 Redis 移除 Token
     */
    @Override
    public void removeToken(Long userId, String token) {
        String key = "user:tokens:" + userId;
        redisUtil.removeFromList(key, token);

        // 如果用户没有其他登录会话，标记为离线
        long remainingTokens = redisUtil.getListSize(key);
        if (remainingTokens == 0) {
            redisUtil.set("user:status:" + userId, "0");
            logger.info(Constants.REMOVE_TOKEN_LOGOUT, userId);
        } else {
            logger.info(Constants.REMOVE_TOKEN, userId, remainingTokens);
        }
    }

    /**
     * 验证 Token 是否有效且在 Redis 列表中
     * 
     * @return true 表示 Token 有效且在列表中；false 表示无效或不在列表中
     */
    @Override
    public boolean validateTokenInRedis(Long userId, String token) {
        String key = "user:tokens:" + userId;

        // 1. 检查 Token 是否在 Redis 列表中
        if (!redisUtil.existsInList(key, token)) {
            logger.debug(Constants.TOKEN_REDIS, userId);
            return false;
        }

        // 2. 验证 Token 是否过期或格式错误
        try {
            if (!jwtUtil.validateToken(token)) {
                logger.debug(Constants.TOKEN_EXPIRED_CLEAN, userId);
                removeToken(userId, token);
                return false;
            }
        } catch (Exception e) {
            logger.error(Constants.VERIFY_TOKEN, userId, e);
            removeToken(userId, token);
            return false;
        }

        return true;
    }

    /**
     * 获取用户在线设备数（登录会话数）
     */
    @Override
    public long getUserOnlineDeviceCount(Long userId) {
        String key = "user:tokens:" + userId;
        return redisUtil.getListSize(key);
    }

    /**
     * 获取用户所有登录 Token
     */
    @Override
    public List<String> getUserTokens(Long userId) {
        String key = "user:tokens:" + userId;
        return redisUtil.getList(key);
    }

    /**
     * 手动下线用户：删除该用户的所有 Token
     */
    @Override
    public void forceLogoutUser(Long userId) {
        String key = "user:tokens:" + userId;
        List<String> tokens = redisUtil.getList(key);

        // 清空列表
        redisUtil.clearList(key);

        // 标记用户为离线
        redisUtil.set("user:status:" + userId, "0");

        logger.info(Constants.ADMIN_TOKEN_CLEAN, userId, tokens.size());
    }

    /**
     * 踢出其他设备：清除该用户除 currentToken 外的所有 Token
     */
    @Override
    public int removeOtherTokens(Long userId, String currentToken) {
        String key = "user:tokens:" + userId;

        // 如果当前 token 不在列表里（例如 Redis 丢失/重启），先补回去，确保“保留当前 token”的语义成立
        if (!redisUtil.existsInList(key, currentToken)) {
            redisUtil.addToList(key, currentToken);
            redisUtil.expire(key, 24 * 60 * 60);
            redisUtil.set("user:status:" + userId, "1", 24 * 60 * 60);
        }

        List<String> tokens = redisUtil.getList(key);
        int removed = 0;
        for (String token : tokens) {
            if (token != null && !token.equals(currentToken)) {
                redisUtil.removeFromList(key, token);
                removed++;
            }
        }

        // 如果列表空了，标记离线
        long remaining = redisUtil.getListSize(key);
        if (remaining == 0) {
            redisUtil.set("user:status:" + userId, "0");
        }

        return removed;
    }

    /**
     * 定时任务：检查并清理所有过期的 Token
     */
    @Override
    public void cleanupExpiredTokens() {
        // 扫描所有 user:tokens:* 的 key
        Set<String> keys = redisUtil.getKeys("user:tokens:*");
        if (keys == null || keys.isEmpty()) {
            logger.info(Constants.TASK_NO_CLEAN);
            return;
        }

        int totalCleaned = 0;
        int totalUsers = keys.size();

        for (String key : keys) {
            List<String> tokens = redisUtil.getList(key);
            int cleanedForUser = 0;

            for (String token : tokens) {
                try {
                    // 检查 Token 是否过期
                    if (!jwtUtil.validateToken(token)) {
                        // 过期则移除
                        redisUtil.removeFromList(key, token);
                        totalCleaned++;
                        cleanedForUser++;
                        logger.debug(Constants.REMOVE_EXPIRED_TOKEN, token.substring(0, Math.min(20, token.length())) + "...");
                    }
                } catch (Exception e) {
                    // 格式错误的 Token 也直接移除
                    redisUtil.removeFromList(key, token);
                    totalCleaned++;
                    cleanedForUser++;
                    logger.debug(Constants.REMOVE_INVALID_TOKEN, token.substring(0, Math.min(20, token.length())) + "...");
                }
            }

            // 如果该用户没有有效的 Token，标记为离线
            long remainingCount = redisUtil.getListSize(key);
            if (remainingCount == 0) {
                try {
                    Long userId = Long.parseLong(key.replace("user:tokens:", ""));
                    redisUtil.set("user:status:" + userId, "0");
                    logger.debug(Constants.NO_TOKEN_LOGOUT, userId);
                } catch (NumberFormatException e) {
                    logger.error(Constants.EXPIRED_USER_FAIL, key);
                }
            }

            if (cleanedForUser > 0) {
                logger.info(Constants.USER_TOKEN_CLEAN, key, cleanedForUser);
            }
        }

        logger.info(Constants.TOTAL_CLEAN, totalUsers, totalCleaned);
    }
}

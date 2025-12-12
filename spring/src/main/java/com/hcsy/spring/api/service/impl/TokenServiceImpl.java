package com.hcsy.spring.api.service.impl;

import com.hcsy.spring.api.service.TokenService;
import com.hcsy.spring.common.utils.RedisUtil;
import com.hcsy.spring.common.utils.SimpleLogger;
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

        logger.info("用户 %d 登录，Token 已保存到 Redis", userId);
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
            logger.info("用户 %d 没有其他登录会话，状态已设为离线", userId);
        } else {
            logger.info("用户 %d 登出，还有 %d 个登录会话", userId, remainingTokens);
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
            logger.debug("用户 %d 的 Token 不在 Redis 列表中，可能已被管理员踢下线", userId);
            return false;
        }

        // 2. 验证 Token 是否过期或格式错误
        try {
            if (!jwtUtil.validateToken(token)) {
                logger.debug("用户 %d 的 Token 已过期或格式错误，将从 Redis 列表中移除", userId);
                removeToken(userId, token);
                return false;
            }
        } catch (Exception e) {
            logger.error("验证用户 %d 的 Token 时出错", userId, e);
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

        logger.info("管理员已将用户 %d 下线，共清除 %d 个登录会话", userId, tokens.size());
    }

    /**
     * 定时任务：检查并清理所有过期的 Token
     */
    @Override
    public void cleanupExpiredTokens() {
        // 扫描所有 user:tokens:* 的 key
        Set<String> keys = redisUtil.getKeys("user:tokens:*");
        if (keys == null || keys.isEmpty()) {
            logger.info("定时任务：没有需要清理的 Token");
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
                        logger.debug("移除过期 Token: %s", token.substring(0, Math.min(20, token.length())) + "...");
                    }
                } catch (Exception e) {
                    // 格式错误的 Token 也直接移除
                    redisUtil.removeFromList(key, token);
                    totalCleaned++;
                    cleanedForUser++;
                    logger.debug("移除无效 Token: %s", token.substring(0, Math.min(20, token.length())) + "...");
                }
            }

            // 如果该用户没有有效的 Token，标记为离线
            long remainingCount = redisUtil.getListSize(key);
            if (remainingCount == 0) {
                try {
                    Long userId = Long.parseLong(key.replace("user:tokens:", ""));
                    redisUtil.set("user:status:" + userId, "0");
                    logger.debug("用户 %d 没有有效 Token，已标记为离线", userId);
                } catch (NumberFormatException e) {
                    logger.error("解析用户 ID 失败: %s", key);
                }
            }

            if (cleanedForUser > 0) {
                logger.info("用户 %s 清理了 %d 个 Token", key, cleanedForUser);
            }
        }

        logger.info("定时任务：清理完成，扫描 %d 个用户，共清除 %d 个过期 Token", totalUsers, totalCleaned);
    }
}

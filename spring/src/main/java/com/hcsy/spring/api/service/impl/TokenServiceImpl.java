package com.hcsy.spring.api.service.impl;

import java.util.ArrayList;
import java.util.List;
import java.util.Set;

import org.springframework.stereotype.Service;

import com.hcsy.spring.api.service.TokenService;
import com.hcsy.spring.common.exceptions.BusinessException;
import com.hcsy.spring.common.utils.Constants;
import com.hcsy.spring.common.utils.HttpCode;
import com.hcsy.spring.common.utils.JwtUtil;
import com.hcsy.spring.common.utils.RedisUtil;
import com.hcsy.spring.common.utils.SimpleLogger;
import com.hcsy.spring.entity.vo.TokenRefreshVO;
import com.hcsy.spring.entity.vo.UserLoginVO;

import lombok.RequiredArgsConstructor;

/**
 * Token 管理服务实现
 * 基于 session 的双 token 机制，使用 Redis Hash/Set 存储会话关系
 */
@Service
@RequiredArgsConstructor
public class TokenServiceImpl implements TokenService {
    private final SimpleLogger logger;
    private final RedisUtil redisUtil;
    private final JwtUtil jwtUtil;

    @Override
    public UserLoginVO createLoginSession(Long userId, String username) {
        String sessionId = jwtUtil.generateSessionId();

        // 1. 生成 access token 和 refresh token
        String accessToken = jwtUtil.generateAccessToken(userId, username, sessionId);
        String refreshToken = jwtUtil.generateRefreshToken(userId, username, sessionId);

        long accessTtl = jwtUtil.getAccessExpirationSeconds();
        long refreshTtl = jwtUtil.getRefreshExpirationSeconds();

        // 2. 写入 session hash
        String sessionKey = "user:session:" + userId + ":" + sessionId;
        redisUtil.putHash(sessionKey, "accessToken", accessToken);
        redisUtil.putHash(sessionKey, "refreshToken", refreshToken);
        redisUtil.putHash(sessionKey, "username", username);
        redisUtil.putHash(sessionKey, "createTime", String.valueOf(System.currentTimeMillis()));
        redisUtil.expire(sessionKey, refreshTtl);

        // 3. 写入 access 反查 key
        redisUtil.set("user:access:" + accessToken, userId + ":" + sessionId, accessTtl);

        // 4. 写入 refresh 反查 key
        redisUtil.set("user:refresh:" + refreshToken, userId + ":" + sessionId, refreshTtl);

        // 5. 加入用户 session 列表
        String sessionsKey = "user:sessions:" + userId;
        redisUtil.addToSet(sessionsKey, sessionId);
        redisUtil.expire(sessionsKey, refreshTtl);

        // 6. 标记用户在线
        redisUtil.set("user:status:" + userId, "1");

        // 7. 获取在线设备数
        long deviceCount = getUserOnlineDeviceCount(userId);

        logger.info(Constants.LOGIN_SESSION_CREATED, userId, sessionId);

        return UserLoginVO.builder()
                .accessToken(accessToken)
                .refreshToken(refreshToken)
                .tokenType("Bearer")
                .expiresIn(accessTtl)
                .refreshExpiresIn(refreshTtl)
                .userId(userId)
                .username(username)
                .sessionId(sessionId)
                .onlineDeviceCount(deviceCount)
                .build();
    }

    @Override
    public TokenRefreshVO refreshToken(String refreshToken) {
        // 1. 校验 refresh token JWT
        jwtUtil.validateRefreshToken(refreshToken);

        Long userId = jwtUtil.extractUserId(refreshToken);
        String sessionId = jwtUtil.extractSessionId(refreshToken);

        // 2. 通过 refresh 反查 key 校验
        String refreshKey = "user:refresh:" + refreshToken;
        String storedValue = redisUtil.get(refreshKey);
        if (storedValue == null) {
            throw new BusinessException(HttpCode.UNAUTHORIZED, Constants.REFRESH_TOKEN_INVALID);
        }

        String expectedValue = userId + ":" + sessionId;
        if (!expectedValue.equals(storedValue)) {
            throw new BusinessException(HttpCode.UNAUTHORIZED, Constants.REFRESH_TOKEN_INVALID);
        }

        // 3. 校验 session hash 存在且 refresh token 一致
        String sessionKey = "user:session:" + userId + ":" + sessionId;
        if (!redisUtil.exists(sessionKey)) {
            throw new BusinessException(HttpCode.UNAUTHORIZED, Constants.SESSION_NOT_FOUND);
        }

        String storedRefreshToken = redisUtil.getHash(sessionKey, "refreshToken");
        if (!refreshToken.equals(storedRefreshToken)) {
            throw new BusinessException(HttpCode.UNAUTHORIZED, Constants.REFRESH_TOKEN_INVALID);
        }

        String username = redisUtil.getHash(sessionKey, "username");

        // 4. 获取旧的 access token 并删除
        String oldAccessToken = redisUtil.getHash(sessionKey, "accessToken");
        if (oldAccessToken != null) {
            redisUtil.delete("user:access:" + oldAccessToken);
        }

        // 5. 删除旧的 refresh 反查 key
        redisUtil.delete(refreshKey);

        // 6. 生成新的 token
        String newAccessToken = jwtUtil.generateAccessToken(userId, username, sessionId);
        String newRefreshToken = jwtUtil.generateRefreshToken(userId, username, sessionId);

        long accessTtl = jwtUtil.getAccessExpirationSeconds();
        long refreshTtl = jwtUtil.getRefreshExpirationSeconds();

        // 7. 更新 session hash
        redisUtil.putHash(sessionKey, "accessToken", newAccessToken);
        redisUtil.putHash(sessionKey, "refreshToken", newRefreshToken);
        redisUtil.expire(sessionKey, refreshTtl);

        // 8. 写入新的反查 key
        redisUtil.set("user:access:" + newAccessToken, userId + ":" + sessionId, accessTtl);
        redisUtil.set("user:refresh:" + newRefreshToken, userId + ":" + sessionId, refreshTtl);

        // 9. 刷新 session 列表 TTL
        String sessionsKey = "user:sessions:" + userId;
        redisUtil.expire(sessionsKey, refreshTtl);

        // 10. 确保用户在线
        redisUtil.set("user:status:" + userId, "1");

        logger.info(Constants.REFRESH_TOKEN_SUCCESS);

        return TokenRefreshVO.builder()
                .accessToken(newAccessToken)
                .refreshToken(newRefreshToken)
                .tokenType("Bearer")
                .expiresIn(accessTtl)
                .refreshExpiresIn(refreshTtl)
                .userId(userId)
                .username(username)
                .sessionId(sessionId)
                .build();
    }

    @Override
    public void removeSessionByAccessToken(String accessToken) {
        String accessKey = "user:access:" + accessToken;
        String storedValue = redisUtil.get(accessKey);
        if (storedValue == null) {
            return;
        }

        String[] parts = storedValue.split(":", 2);
        if (parts.length != 2) {
            return;
        }

        Long userId = Long.parseLong(parts[0]);
        String sessionId = parts[1];

        removeSession(userId, sessionId);
    }

    @Override
    public void removeSession(Long userId, String sessionId) {
        String sessionKey = "user:session:" + userId + ":" + sessionId;

        // 1. 获取 access/refresh token
        String accessToken = redisUtil.getHash(sessionKey, "accessToken");
        String refreshToken = redisUtil.getHash(sessionKey, "refreshToken");

        // 2. 删除反查 key
        if (accessToken != null) {
            redisUtil.delete("user:access:" + accessToken);
        }
        if (refreshToken != null) {
            redisUtil.delete("user:refresh:" + refreshToken);
        }

        // 3. 删除 session hash
        redisUtil.delete(sessionKey);

        // 4. 从 session 列表移除
        String sessionsKey = "user:sessions:" + userId;
        redisUtil.removeFromSet(sessionsKey, sessionId);

        // 5. 检查是否还有 session
        long remainingSessions = redisUtil.getSetSize(sessionsKey);
        if (remainingSessions == 0) {
            redisUtil.set("user:status:" + userId, "0");
            redisUtil.delete(sessionsKey);
            logger.info(Constants.REMOVE_SESSION_LOGOUT, userId);
        } else {
            logger.info(Constants.REMOVE_SESSION, userId, remainingSessions);
        }

        logger.info(Constants.LOGIN_SESSION_REMOVED, userId, sessionId);
    }

    @Override
    public boolean validateAccessTokenInRedis(Long userId, String sessionId, String accessToken) {
        // 1. 检查 access 反查 key
        String accessKey = "user:access:" + accessToken;
        String storedValue = redisUtil.get(accessKey);
        if (storedValue == null) {
            return false;
        }

        String expectedValue = userId + ":" + sessionId;
        if (!expectedValue.equals(storedValue)) {
            return false;
        }

        // 2. 检查 session hash 是否存在
        String sessionKey = "user:session:" + userId + ":" + sessionId;
        if (!redisUtil.exists(sessionKey)) {
            return false;
        }

        // 3. 检查 session 中的 access token 是否匹配
        String storedAccessToken = redisUtil.getHash(sessionKey, "accessToken");
        return accessToken.equals(storedAccessToken);
    }

    @Override
    public long getUserOnlineDeviceCount(Long userId) {
        String sessionsKey = "user:sessions:" + userId;
        return redisUtil.getSetSize(sessionsKey);
    }

    @Override
    public List<String> getUserSessions(Long userId) {
        String sessionsKey = "user:sessions:" + userId;
        Set<String> sessions = redisUtil.getSet(sessionsKey);
        return sessions != null ? new ArrayList<>(sessions) : new ArrayList<>();
    }

    @Override
    public void forceLogoutUser(Long userId) {
        String sessionsKey = "user:sessions:" + userId;
        Set<String> sessionIds = redisUtil.getSet(sessionsKey);

        if (sessionIds != null) {
            for (String sessionId : sessionIds) {
                removeSession(userId, sessionId);
            }
        }

        // 额外确保状态为离线
        redisUtil.set("user:status:" + userId, "0");

        logger.info(Constants.ADMIN_SESSION_CLEAN, userId, sessionIds != null ? sessionIds.size() : 0);
    }

    @Override
    public int removeOtherSessions(Long userId, String currentAccessToken) {
        // 从当前 access token 解析 sessionId
        String sessionId = jwtUtil.extractSessionId(currentAccessToken);

        String sessionsKey = "user:sessions:" + userId;
        Set<String> sessionIds = redisUtil.getSet(sessionsKey);

        int removed = 0;
        if (sessionIds != null) {
            for (String sid : sessionIds) {
                if (!sid.equals(sessionId)) {
                    removeSession(userId, sid);
                    removed++;
                }
            }
        }

        // 确保当前 session 的 user:status 正确
        long remaining = redisUtil.getSetSize(sessionsKey);
        if (remaining > 0) {
            redisUtil.set("user:status:" + userId, "1");
            redisUtil.expire(sessionsKey, jwtUtil.getRefreshExpirationSeconds());
        }

        return removed;
    }

    @Override
    public void cleanupExpiredTokens() {
        // 扫描所有 user:sessions:* 的 key
        Set<String> sessionKeys = redisUtil.getKeys("user:sessions:*");
        if (sessionKeys == null || sessionKeys.isEmpty()) {
            logger.info(Constants.TASK_NO_CLEAN_SESSION);
            return;
        }

        int totalCleaned = 0;
        int totalUsers = sessionKeys.size();

        for (String key : sessionKeys) {
            try {
                Long userId = Long.parseLong(key.replace("user:sessions:", ""));
                Set<String> sessionIds = redisUtil.getSet(key);
                int cleanedForUser = 0;

                if (sessionIds == null || sessionIds.isEmpty()) {
                    redisUtil.set("user:status:" + userId, "0");
                    redisUtil.delete(key);
                    continue;
                }

                List<String> toRemove = new ArrayList<>();

                for (String sessionId : sessionIds) {
                    String sessionKey = "user:session:" + userId + ":" + sessionId;

                    // 检查 session hash 是否存在
                    if (!redisUtil.exists(sessionKey)) {
                        toRemove.add(sessionId);
                        cleanedForUser++;
                        continue;
                    }

                    // 检查 refresh token
                    String refreshToken = redisUtil.getHash(sessionKey, "refreshToken");
                    if (refreshToken == null || refreshToken.isEmpty()) {
                        toRemove.add(sessionId);
                        cleanedForUser++;
                        cleanSessionKeys(userId, sessionId, sessionKey);
                        continue;
                    }

                    // 校验 refresh token 是否有效
                    String refreshKey = "user:refresh:" + refreshToken;
                    String storedValue = redisUtil.get(refreshKey);
                    if (storedValue == null || !storedValue.equals(userId + ":" + sessionId)) {
                        toRemove.add(sessionId);
                        cleanedForUser++;
                        cleanSessionKeys(userId, sessionId, sessionKey);
                        continue;
                    }

                    // 校验 access token
                    String accessToken = redisUtil.getHash(sessionKey, "accessToken");
                    if (accessToken != null) {
                        String accessKey = "user:access:" + accessToken;
                        if (!redisUtil.exists(accessKey)) {
                            // access 反查 key 不存在，可能是 TTL 过期，补写
                            long remainingMs = jwtUtil.getRemainingTime(accessToken);
                            long remainingSec = remainingMs > 0 ? remainingMs / 1000 : 0;
                            if (remainingSec > 0) {
                                redisUtil.set(accessKey, userId + ":" + sessionId, remainingSec);
                            }
                        }
                    }
                }

                // 移除已清理的 session
                for (String sid : toRemove) {
                    redisUtil.removeFromSet(key, sid);
                }

                // 更新状态
                long remainingSessions = redisUtil.getSetSize(key);
                if (remainingSessions == 0) {
                    redisUtil.set("user:status:" + userId, "0");
                    redisUtil.delete(key);
                } else {
                    redisUtil.set("user:status:" + userId, "1");
                }

                if (cleanedForUser > 0) {
                    logger.info(Constants.SESSION_CLEAN_LOG, key, cleanedForUser);
                }

                totalCleaned += cleanedForUser;
            } catch (Exception e) {
                logger.error(Constants.EXPIRED_USER_FAIL + key);
            }
        }

        logger.info(Constants.TOTAL_SESSION_CLEAN, totalUsers, totalCleaned);
    }

    private void cleanSessionKeys(Long userId, String sessionId, String sessionKey) {
        String accessToken = redisUtil.getHash(sessionKey, "accessToken");
        String refreshToken = redisUtil.getHash(sessionKey, "refreshToken");
        if (accessToken != null) {
            redisUtil.delete("user:access:" + accessToken);
        }
        if (refreshToken != null) {
            redisUtil.delete("user:refresh:" + refreshToken);
        }
        redisUtil.delete(sessionKey);
    }
}

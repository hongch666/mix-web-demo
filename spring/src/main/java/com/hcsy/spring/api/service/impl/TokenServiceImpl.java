package com.hcsy.spring.api.service.impl;

import java.util.List;
import java.util.UUID;

import org.springframework.stereotype.Service;

import com.hcsy.spring.api.service.TokenService;
import com.hcsy.spring.common.constants.HttpCode;
import com.hcsy.spring.common.constants.Messages;
import com.hcsy.spring.common.constants.RedisKeys;
import com.hcsy.spring.common.exceptions.BusinessException;
import com.hcsy.spring.common.utils.JwtUtil;
import com.hcsy.spring.common.utils.RedisUtil;
import com.hcsy.spring.common.utils.SimpleLogger;
import com.hcsy.spring.entity.vo.TokenRefreshVO;
import com.hcsy.spring.entity.vo.UserLoginVO;

import lombok.RequiredArgsConstructor;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

@Service
@RequiredArgsConstructor
public class TokenServiceImpl implements TokenService {

    private final RedisUtil redisUtil;
    private final JwtUtil jwtUtil;
    private final SimpleLogger logger;

    @Override
    public Mono<UserLoginVO> createLoginSession(Long userId, String username) {
        String sessionId = UUID.randomUUID().toString().replace("-", "");
        String accessToken = jwtUtil.generateAccessToken(userId, username, sessionId);
        String refreshToken = jwtUtil.generateRefreshToken(userId, username, sessionId);
        long accessTtl = jwtUtil.getAccessExpirationSeconds();
        long refreshTtl = jwtUtil.getRefreshExpirationSeconds();
        String sessionKey = sessionKey(userId, sessionId);
        String sessionsKey = sessionsKey(userId);

        Mono<Void> sessionWrite = Mono.when(
                redisUtil.putHash(sessionKey, "accessToken", accessToken),
                redisUtil.putHash(sessionKey, "refreshToken", refreshToken),
                redisUtil.putHash(sessionKey, "username", username))
                .then(redisUtil.expire(sessionKey, refreshTtl))
                .then();
        Mono<Void> reverseIndexes = Mono.when(
                redisUtil.set(accessKey(accessToken), userId + ":" + sessionId, accessTtl),
                redisUtil.set(refreshKey(refreshToken), userId + ":" + sessionId, refreshTtl));
        Mono<Void> sessionSet = redisUtil.addToSet(sessionsKey, sessionId)
                .then(redisUtil.expire(sessionsKey, refreshTtl))
                .then();

        return Mono.when(sessionWrite, reverseIndexes, sessionSet,
                redisUtil.set(RedisKeys.userStatus(userId), "1"))
                .then(redisUtil.getSetSize(sessionsKey))
                .map(deviceCount -> {
                    logger.info(Messages.LOGIN_SESSION_CREATED, userId, sessionId);
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
                });
    }

    @Override
    public Mono<TokenRefreshVO> refreshToken(String refreshToken) {
        jwtUtil.validateRefreshToken(refreshToken);
        Long userId = jwtUtil.extractUserId(refreshToken);
        String sessionId = jwtUtil.extractSessionId(refreshToken);
        String sessionKey = sessionKey(userId, sessionId);
        String expectedValue = userId + ":" + sessionId;

        Mono<String> reverseValue = redisUtil.get(refreshKey(refreshToken)).defaultIfEmpty("");
        Mono<String> storedRefreshToken = redisUtil.getHash(sessionKey, "refreshToken").defaultIfEmpty("");
        Mono<String> username = redisUtil.getHash(sessionKey, "username").defaultIfEmpty("");
        Mono<String> oldAccessToken = redisUtil.getHash(sessionKey, "accessToken").defaultIfEmpty("");

        return Mono.zip(reverseValue, storedRefreshToken, username, oldAccessToken)
                .flatMap(values -> {
                    if (!expectedValue.equals(values.getT1()) || !refreshToken.equals(values.getT2())) {
                        return Mono.error(unauthorized(Messages.REFRESH_TOKEN_INVALID));
                    }
                    if (values.getT3().isEmpty()) {
                        return Mono.error(unauthorized(Messages.SESSION_NOT_FOUND));
                    }
                    return rotateTokens(userId, sessionId, values.getT3(), refreshToken, values.getT4());
                });
    }

    private Mono<TokenRefreshVO> rotateTokens(
            Long userId, String sessionId, String username, String oldRefreshToken, String oldAccessToken) {
        String newAccessToken = jwtUtil.generateAccessToken(userId, username, sessionId);
        String newRefreshToken = jwtUtil.generateRefreshToken(userId, username, sessionId);
        long accessTtl = jwtUtil.getAccessExpirationSeconds();
        long refreshTtl = jwtUtil.getRefreshExpirationSeconds();
        String sessionKey = sessionKey(userId, sessionId);

        Mono<Void> deleteOldIndexes = Mono.when(
                oldAccessToken.isEmpty() ? Mono.empty() : redisUtil.delete(accessKey(oldAccessToken)),
                redisUtil.delete(refreshKey(oldRefreshToken)));
        Mono<Void> updateSession = Mono.when(
                redisUtil.putHash(sessionKey, "accessToken", newAccessToken),
                redisUtil.putHash(sessionKey, "refreshToken", newRefreshToken))
                .then(redisUtil.expire(sessionKey, refreshTtl))
                .then();
        Mono<Void> writeIndexes = Mono.when(
                redisUtil.set(accessKey(newAccessToken), userId + ":" + sessionId, accessTtl),
                redisUtil.set(refreshKey(newRefreshToken), userId + ":" + sessionId, refreshTtl),
                redisUtil.expire(sessionsKey(userId), refreshTtl),
                redisUtil.set(RedisKeys.userStatus(userId), "1"));

        return deleteOldIndexes.then(Mono.when(updateSession, writeIndexes)).then(Mono.fromSupplier(() -> {
            logger.info(Messages.REFRESH_TOKEN_SUCCESS);
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
        }));
    }

    @Override
    public Mono<Void> removeSessionByAccessToken(String accessToken) {
        return redisUtil.get(accessKey(accessToken))
                .flatMap(value -> {
                    String[] parts = value.split(":", 2);
                    if (parts.length != 2) {
                        return Mono.empty();
                    }
                    return removeSession(Long.parseLong(parts[0]), parts[1]);
                })
                .then();
    }

    @Override
    public Mono<Void> removeSession(Long userId, String sessionId) {
        String sessionKey = sessionKey(userId, sessionId);
        Mono<String> accessToken = redisUtil.getHash(sessionKey, "accessToken").defaultIfEmpty("");
        Mono<String> refreshToken = redisUtil.getHash(sessionKey, "refreshToken").defaultIfEmpty("");

        return Mono.zip(accessToken, refreshToken).flatMap(tokens -> {
            Mono<Void> deleteIndexes = Mono.when(
                    tokens.getT1().isEmpty() ? Mono.empty() : redisUtil.delete(accessKey(tokens.getT1())),
                    tokens.getT2().isEmpty() ? Mono.empty() : redisUtil.delete(refreshKey(tokens.getT2())));
            return Mono.when(
                    deleteIndexes,
                    redisUtil.delete(sessionKey),
                    redisUtil.removeFromSet(sessionsKey(userId), sessionId))
                    .then(redisUtil.getSetSize(sessionsKey(userId)))
                    .flatMap(remaining -> {
                        logger.info(Messages.LOGIN_SESSION_REMOVED, userId, sessionId);
                        if (remaining == 0) {
                            logger.info(Messages.REMOVE_SESSION_LOGOUT, userId);
                            return Mono.when(
                                    redisUtil.set(RedisKeys.userStatus(userId), "0"),
                                    redisUtil.delete(sessionsKey(userId))).then();
                        }
                        logger.info(Messages.REMOVE_SESSION, userId, remaining);
                        return Mono.empty();
                    });
        });
    }

    @Override
    public Mono<Boolean> validateAccessTokenInRedis(Long userId, String sessionId, String accessToken) {
        String expectedValue = userId + ":" + sessionId;
        return Mono.zip(
                redisUtil.get(accessKey(accessToken)).defaultIfEmpty(""),
                redisUtil.getHash(sessionKey(userId, sessionId), "accessToken").defaultIfEmpty(""))
                .map(values -> expectedValue.equals(values.getT1()) && accessToken.equals(values.getT2()));
    }

    @Override
    public Mono<Long> getUserOnlineDeviceCount(Long userId) {
        return redisUtil.getSetSize(sessionsKey(userId));
    }

    @Override
    public Mono<List<String>> getUserSessions(Long userId) {
        return redisUtil.getSet(sessionsKey(userId));
    }

    @Override
    public Mono<Void> forceLogoutUser(Long userId) {
        return redisUtil.getSet(sessionsKey(userId))
                .flatMapMany(Flux::fromIterable)
                .flatMap(sessionId -> removeSession(userId, sessionId), 8)
                .then(redisUtil.set(RedisKeys.userStatus(userId), "0"))
                .doOnSuccess(ignored -> logger.info(Messages.ADMIN_SESSION_CLEAN, userId, 0))
                .then();
    }

    @SuppressWarnings("null")
    @Override
    public Mono<Integer> removeOtherSessions(Long userId, String currentAccessToken) {
        String currentSessionId = jwtUtil.extractSessionId(currentAccessToken);
        return redisUtil.getSet(sessionsKey(userId))
                .flatMapMany(Flux::fromIterable)
                .filter(sessionId -> !sessionId.equals(currentSessionId))
                .flatMap(sessionId -> removeSession(userId, sessionId).thenReturn(1), 8)
                .reduce(0, Integer::sum)
                .flatMap(removed -> redisUtil.getSetSize(sessionsKey(userId))
                        .flatMap(remaining -> remaining > 0
                                ? Mono.when(
                                        redisUtil.set(RedisKeys.userStatus(userId), "1"),
                                        redisUtil.expire(sessionsKey(userId), jwtUtil.getRefreshExpirationSeconds()))
                                        .thenReturn(removed)
                                : Mono.just(removed)));
    }

    @SuppressWarnings("null")
    @Override
    public Mono<Void> cleanupExpiredTokens() {
        return redisUtil.getKeys("user:sessions:*")
                .flatMap(this::cleanupUserSessions, 4)
                .reduce(0, Integer::sum)
                .doOnNext(cleaned -> logger.info(Messages.TOTAL_SESSION_CLEAN, 0, cleaned))
                .then();
    }

    @SuppressWarnings("null")
    private Mono<Integer> cleanupUserSessions(String key) {
        Long userId;
        try {
            userId = Long.parseLong(key.substring("user:sessions:".length()));
        } catch (RuntimeException error) {
            logger.error(Messages.EXPIRED_USER_FAIL + key, error);
            return Mono.just(0);
        }

        return redisUtil.getSet(key)
                .flatMapMany(Flux::fromIterable)
                .flatMap(sessionId -> isSessionValid(userId, sessionId)
                        .filter(Boolean.FALSE::equals)
                        .flatMap(ignored -> removeSession(userId, sessionId).thenReturn(1)), 8)
                .reduce(0, Integer::sum)
                .doOnNext(cleaned -> {
                    if (cleaned > 0) {
                        logger.info(Messages.SESSION_CLEAN_LOG, key, cleaned);
                    }
                })
                .onErrorResume(error -> {
                    logger.error(Messages.EXPIRED_USER_FAIL + key, error);
                    return Mono.just(0);
                });
    }

    private Mono<Boolean> isSessionValid(Long userId, String sessionId) {
        String sessionKey = sessionKey(userId, sessionId);
        return redisUtil.getHash(sessionKey, "refreshToken")
                .flatMap(refreshToken -> redisUtil.get(refreshKey(refreshToken))
                        .map(value -> value.equals(userId + ":" + sessionId)))
                .defaultIfEmpty(false);
    }

    private String sessionKey(Long userId, String sessionId) {
        return "user:session:" + userId + ":" + sessionId;
    }

    private String sessionsKey(Long userId) {
        return "user:sessions:" + userId;
    }

    private String accessKey(String accessToken) {
        return "user:access:" + accessToken;
    }

    private String refreshKey(String refreshToken) {
        return "user:refresh:" + refreshToken;
    }

    private BusinessException unauthorized(String message) {
        return BusinessException.builder().httpStatus(HttpCode.UNAUTHORIZED).errorMessage(message).build();
    }
}

package com.hcsy.spring.api.service.impl;

import java.net.URLDecoder;
import java.nio.charset.StandardCharsets;
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
import com.hcsy.spring.entity.dto.AuthIdentityDTO;

import lombok.RequiredArgsConstructor;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

@Service
@RequiredArgsConstructor
public class TokenServiceImpl implements TokenService {
    private static final String BEARER_PREFIX = "Bearer ";


    private final RedisUtil redisUtil;
    private final JwtUtil jwtUtil;
    private final SimpleLogger logger;

    @Override
    public Mono<AuthIdentityDTO> validateAccessToken(String accessToken) {
        return Mono.defer(() -> {
            jwtUtil.validateAccessToken(accessToken);

            Long userId = jwtUtil.extractUserId(accessToken);
            String sessionId = jwtUtil.extractSessionId(accessToken);
            String sessionKey = RedisKeys.userSession(userId, sessionId);
            String expectedValue = userId + ":" + sessionId;

            Mono<String> accessIndex = redisUtil.get(RedisKeys.userAccess(accessToken)).defaultIfEmpty("");
            Mono<String> storedAccessToken = redisUtil.getHash(sessionKey, "accessToken").defaultIfEmpty("");
            Mono<String> sessionUsername = redisUtil.getHash(sessionKey, "username").defaultIfEmpty("");
            Mono<String> userStatus = redisUtil.get(RedisKeys.userStatus(userId)).defaultIfEmpty("");

            return Mono.zip(accessIndex, storedAccessToken, sessionUsername, userStatus)
                .flatMap(values -> {
                    if (!expectedValue.equals(values.getT1())
                        || !accessToken.equals(values.getT2())
                        || "0".equals(values.getT4())) {
                        logger.warning(Messages.USER_NOT_LOGIN);
                        return Mono.error(unauthorized(Messages.USER_NOT_LOGIN));
                    }

                    String username = values.getT3().isEmpty()
                        ? jwtUtil.extractUsername(accessToken)
                        : values.getT3();
                    logger.debug(Messages.AUTH_IDENTITY_RESOLVED, userId, sessionId);
                    return Mono.just(new AuthIdentityDTO(userId, username, sessionId));
                });
        });
    }

    @Override
    public Mono<AuthIdentityDTO> validateGatewayAccessToken(
        String authorization, String accessToken, String forwardedUri) {
        String token = extractGatewayAccessToken(authorization, accessToken, forwardedUri);
        if (token == null) {
            return Mono.error(unauthorized(Messages.USER_NOT_LOGIN));
        }
        return validateAccessToken(token);
    }

    @Override
    public Mono<UserLoginVO> createLoginSession(Long userId, String username) {
        String sessionId = UUID.randomUUID().toString().replace("-", "");
        String accessToken = jwtUtil.generateAccessToken(userId, username, sessionId);
        String refreshToken = jwtUtil.generateRefreshToken(userId, username, sessionId);
        long accessTtl = jwtUtil.getAccessExpirationSeconds();
        long refreshTtl = jwtUtil.getRefreshExpirationSeconds();
        String sessionKey = RedisKeys.userSession(userId, sessionId);
        String sessionsKey = RedisKeys.userSessions(userId);

        Mono<Void> sessionWrite = Mono.when(
            redisUtil.putHash(sessionKey, "accessToken", accessToken),
            redisUtil.putHash(sessionKey, "refreshToken", refreshToken),
            redisUtil.putHash(sessionKey, "username", username))
            .then(redisUtil.expire(sessionKey, refreshTtl))
            .then();
        Mono<Void> reverseIndexes = Mono.when(
            redisUtil.set(RedisKeys.userAccess(accessToken), userId + ":" + sessionId, accessTtl),
            redisUtil.set(RedisKeys.userRefresh(refreshToken), userId + ":" + sessionId, refreshTtl));
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
        String sessionKey = RedisKeys.userSession(userId, sessionId);
        String expectedValue = userId + ":" + sessionId;

        Mono<String> reverseValue = redisUtil.get(RedisKeys.userRefresh(refreshToken)).defaultIfEmpty("");
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
        String sessionKey = RedisKeys.userSession(userId, sessionId);

        Mono<Void> deleteOldIndexes = Mono.when(
            oldAccessToken.isEmpty() ? Mono.empty() : redisUtil.delete(RedisKeys.userAccess(oldAccessToken)),
            redisUtil.delete(RedisKeys.userRefresh(oldRefreshToken)));
        Mono<Void> updateSession = Mono.when(
            redisUtil.putHash(sessionKey, "accessToken", newAccessToken),
            redisUtil.putHash(sessionKey, "refreshToken", newRefreshToken))
            .then(redisUtil.expire(sessionKey, refreshTtl))
            .then();
        Mono<Void> writeIndexes = Mono.when(
            redisUtil.set(RedisKeys.userAccess(newAccessToken), userId + ":" + sessionId, accessTtl),
            redisUtil.set(RedisKeys.userRefresh(newRefreshToken), userId + ":" + sessionId, refreshTtl),
            redisUtil.expire(RedisKeys.userSessions(userId), refreshTtl),
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
        return redisUtil.get(RedisKeys.userAccess(accessToken))
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
        String sessionKey = RedisKeys.userSession(userId, sessionId);
        Mono<String> accessToken = redisUtil.getHash(sessionKey, "accessToken").defaultIfEmpty("");
        Mono<String> refreshToken = redisUtil.getHash(sessionKey, "refreshToken").defaultIfEmpty("");

        return Mono.zip(accessToken, refreshToken).flatMap(tokens -> {
            Mono<Void> deleteIndexes = Mono.when(
                tokens.getT1().isEmpty() ? Mono.empty() : redisUtil.delete(RedisKeys.userAccess(tokens.getT1())),
                tokens.getT2().isEmpty() ? Mono.empty() : redisUtil.delete(RedisKeys.userRefresh(tokens.getT2())));
            return Mono.when(
                deleteIndexes,
                redisUtil.delete(sessionKey),
                redisUtil.removeFromSet(RedisKeys.userSessions(userId), sessionId))
                .then(redisUtil.getSetSize(RedisKeys.userSessions(userId)))
                .flatMap(remaining -> {
                    logger.info(Messages.LOGIN_SESSION_REMOVED, userId, sessionId);
                    if (remaining == 0) {
                        logger.info(Messages.REMOVE_SESSION_LOGOUT, userId);
                        return Mono.when(
                            redisUtil.set(RedisKeys.userStatus(userId), "0"),
                            redisUtil.delete(RedisKeys.userSessions(userId))).then();
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
            redisUtil.get(RedisKeys.userAccess(accessToken)).defaultIfEmpty(""),
            redisUtil.getHash(RedisKeys.userSession(userId, sessionId), "accessToken").defaultIfEmpty(""))
            .map(values -> expectedValue.equals(values.getT1()) && accessToken.equals(values.getT2()));
    }

    @Override
    public Mono<Long> getUserOnlineDeviceCount(Long userId) {
        return redisUtil.getSetSize(RedisKeys.userSessions(userId));
    }

    @Override
    public Mono<List<String>> getUserSessions(Long userId) {
        return redisUtil.getSet(RedisKeys.userSessions(userId));
    }

    @Override
    public Mono<Void> forceLogoutUser(Long userId) {
        return redisUtil.getSet(RedisKeys.userSessions(userId))
            .flatMapMany(Flux::fromIterable)
            .flatMap(sessionId -> removeSession(userId, sessionId), 8)
            .then(redisUtil.set(RedisKeys.userStatus(userId), "0"))
            .doOnSuccess(ignored -> logger.info(Messages.ADMIN_SESSION_CLEAN, userId, 0))
            .then();
    }

    @Override
    public Mono<Integer> removeOtherSessions(Long userId, String currentAccessToken) {
        String currentSessionId = jwtUtil.extractSessionId(currentAccessToken);
        return redisUtil.getSet(RedisKeys.userSessions(userId))
            .flatMapMany(Flux::fromIterable)
            .filter(sessionId -> !sessionId.equals(currentSessionId))
            .flatMap(sessionId -> removeSession(userId, sessionId).thenReturn(1), 8)
            .reduce(0, Integer::sum)
            .flatMap(removed -> redisUtil.getSetSize(RedisKeys.userSessions(userId))
                .flatMap(remaining -> remaining > 0
                    ? Mono.when(
                        redisUtil.set(RedisKeys.userStatus(userId), "1"),
                        redisUtil.expire(RedisKeys.userSessions(userId), jwtUtil.getRefreshExpirationSeconds()))
                        .thenReturn(removed)
                    : Mono.just(removed)));
    }

    @Override
    public Mono<Void> cleanupExpiredTokens() {
        return redisUtil.getKeys(RedisKeys.userSessionsPattern())
            .flatMap(this::cleanupUserSessions, 4)
            .reduce(0, Integer::sum)
            .doOnNext(cleaned -> logger.info(Messages.TOTAL_SESSION_CLEAN, 0, cleaned))
            .then();
    }

    private Mono<Integer> cleanupUserSessions(String key) {
        Long userId;
        try {
            userId = Long.parseLong(key.substring(RedisKeys.userSessionsPattern().length() - 1));
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
        String sessionKey = RedisKeys.userSession(userId, sessionId);
        return redisUtil.getHash(sessionKey, "refreshToken")
            .flatMap(refreshToken -> redisUtil.get(RedisKeys.userRefresh(refreshToken))
                .map(value -> value.equals(userId + ":" + sessionId)))
            .defaultIfEmpty(false);
    }

    private String extractGatewayAccessToken(String authorization, String accessToken, String forwardedUri) {
        if (authorization != null && !authorization.isBlank()) {
            return authorization.startsWith(BEARER_PREFIX)
                ? authorization.substring(BEARER_PREFIX.length()).trim()
                : authorization.trim();
        }
        if (accessToken != null && !accessToken.isBlank()) {
            return accessToken.trim();
        }
        if (forwardedUri == null) {
            return null;
        }

        int queryStart = forwardedUri.indexOf('?');
        if (queryStart < 0 || queryStart == forwardedUri.length() - 1) {
            return null;
        }
        for (String pair : forwardedUri.substring(queryStart + 1).split("&")) {
            int separator = pair.indexOf('=');
            if (separator > 0 && "token".equals(pair.substring(0, separator))) {
                return URLDecoder.decode(pair.substring(separator + 1), StandardCharsets.UTF_8);
            }
        }
        return null;
    }

    private BusinessException unauthorized(String message) {
        return BusinessException.builder().httpStatus(HttpCode.UNAUTHORIZED).errorMessage(message).build();
    }
}

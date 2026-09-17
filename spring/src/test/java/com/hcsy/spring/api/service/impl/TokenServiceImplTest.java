package com.hcsy.spring.api.service.impl;

import static org.mockito.ArgumentMatchers.anyLong;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import com.hcsy.spring.common.constants.HttpCode;
import com.hcsy.spring.common.constants.RedisKeys;
import com.hcsy.spring.common.exceptions.BusinessException;
import com.hcsy.spring.common.utils.JwtUtil;
import com.hcsy.spring.common.utils.RedisDistributedLock;
import com.hcsy.spring.common.utils.RedisUtil;
import com.hcsy.spring.common.utils.SimpleLogger;

import reactor.core.publisher.Mono;
import reactor.test.StepVerifier;

@ExtendWith(MockitoExtension.class)
class TokenServiceImplTest {

    private static final Long USER_ID = 7L;
    private static final String SESSION_ID = "session-1";
    private static final String OLD_ACCESS_TOKEN = "old-access-token";
    private static final String OLD_REFRESH_TOKEN = "old-refresh-token";
    private static final String NEW_ACCESS_TOKEN = "new-access-token";
    private static final String NEW_REFRESH_TOKEN = "new-refresh-token";
    private static final String LOCK_VALUE = "lock-value";

    @Mock
    private RedisUtil redisUtil;
    @Mock
    private RedisDistributedLock distributedLock;
    @Mock
    private JwtUtil jwtUtil;
    @Mock
    private SimpleLogger logger;

    private TokenServiceImpl tokenService;

    @BeforeEach
    void setUp() {
        tokenService = new TokenServiceImpl(redisUtil, distributedLock, jwtUtil, logger);
    }

    @Test
    @DisplayName("刷新成功时轮换双 Token、删除旧索引并释放锁")
    void rotatesTokensAndReleasesLock() {
        stubRefreshClaims();
        stubLockAcquired();
        stubStoredSession(OLD_REFRESH_TOKEN);
        stubSuccessfulWrites();
        when(jwtUtil.generateAccessToken(USER_ID, "alice", SESSION_ID)).thenReturn(NEW_ACCESS_TOKEN);
        when(jwtUtil.generateRefreshToken(USER_ID, "alice", SESSION_ID)).thenReturn(NEW_REFRESH_TOKEN);
        when(jwtUtil.getAccessExpirationSeconds()).thenReturn(3600L);
        when(jwtUtil.getRefreshExpirationSeconds()).thenReturn(604800L);

        StepVerifier.create(tokenService.refreshToken(OLD_REFRESH_TOKEN))
            .assertNext(result -> {
                org.junit.jupiter.api.Assertions.assertEquals(NEW_ACCESS_TOKEN, result.getAccessToken());
                org.junit.jupiter.api.Assertions.assertEquals(NEW_REFRESH_TOKEN, result.getRefreshToken());
                org.junit.jupiter.api.Assertions.assertEquals(USER_ID, result.getUserId());
                org.junit.jupiter.api.Assertions.assertEquals(SESSION_ID, result.getSessionId());
            })
            .verifyComplete();

        verify(redisUtil).delete(RedisKeys.userAccess(OLD_ACCESS_TOKEN));
        verify(redisUtil).delete(RedisKeys.userRefresh(OLD_REFRESH_TOKEN));
        verify(redisUtil).set(RedisKeys.userRefresh(NEW_REFRESH_TOKEN), USER_ID + ":" + SESSION_ID, 604800L);
        verify(distributedLock).unlock(RedisKeys.lockTokenRefresh(OLD_REFRESH_TOKEN), LOCK_VALUE);
    }

    @Test
    @DisplayName("旧 Refresh Token 已被轮换时拒绝复用并释放锁")
    void rejectsReusedRefreshTokenAndReleasesLock() {
        stubRefreshClaims();
        stubLockAcquired();
        String sessionKey = RedisKeys.userSession(USER_ID, SESSION_ID);
        when(redisUtil.get(RedisKeys.userRefresh(OLD_REFRESH_TOKEN))).thenReturn(Mono.empty());
        when(redisUtil.getHash(sessionKey, "refreshToken")).thenReturn(Mono.just(NEW_REFRESH_TOKEN));
        when(redisUtil.getHash(sessionKey, "username")).thenReturn(Mono.just("alice"));
        when(redisUtil.getHash(sessionKey, "accessToken")).thenReturn(Mono.just(OLD_ACCESS_TOKEN));

        StepVerifier.create(tokenService.refreshToken(OLD_REFRESH_TOKEN))
            .expectErrorMatches(error -> isUnauthorized(error))
            .verify();

        verify(jwtUtil, never()).generateAccessToken(anyLong(), anyString(), anyString());
        verify(distributedLock).unlock(RedisKeys.lockTokenRefresh(OLD_REFRESH_TOKEN), LOCK_VALUE);
    }

    @Test
    @DisplayName("刷新锁未获取时拒绝请求且不执行会话读取")
    void rejectsRefreshWhenLockIsBusy() {
        stubRefreshClaims();
        when(distributedLock.tryLock(anyString(), anyLong())).thenReturn(Mono.empty());

        StepVerifier.create(tokenService.refreshToken(OLD_REFRESH_TOKEN))
            .expectErrorMatches(error -> isUnauthorized(error))
            .verify();

        verify(redisUtil, never()).get(anyString());
        verify(distributedLock, never()).unlock(anyString(), anyString());
    }

    @Test
    @DisplayName("轮换写入失败时仍释放刷新锁并保留原始异常")
    void releasesLockWhenRotationFails() {
        stubRefreshClaims();
        stubLockAcquired();
        stubStoredSession(OLD_REFRESH_TOKEN);
        when(jwtUtil.generateAccessToken(USER_ID, "alice", SESSION_ID)).thenReturn(NEW_ACCESS_TOKEN);
        when(jwtUtil.generateRefreshToken(USER_ID, "alice", SESSION_ID)).thenReturn(NEW_REFRESH_TOKEN);
        when(jwtUtil.getAccessExpirationSeconds()).thenReturn(3600L);
        when(jwtUtil.getRefreshExpirationSeconds()).thenReturn(604800L);
        when(redisUtil.delete(anyString())).thenReturn(Mono.just(true));
        when(redisUtil.putHash(anyString(), anyString(), anyString()))
            .thenReturn(Mono.error(new IllegalStateException("write failed")));
        when(redisUtil.set(anyString(), anyString(), anyLong())).thenReturn(Mono.just(true));
        when(redisUtil.set(anyString(), anyString())).thenReturn(Mono.just(true));
        when(redisUtil.expire(anyString(), anyLong())).thenReturn(Mono.just(true));

        StepVerifier.create(tokenService.refreshToken(OLD_REFRESH_TOKEN))
            .expectErrorMatches(error -> error instanceof IllegalStateException
                && "write failed".equals(error.getMessage()))
            .verify();

        verify(distributedLock).unlock(RedisKeys.lockTokenRefresh(OLD_REFRESH_TOKEN), LOCK_VALUE);
    }

    @Test
    @DisplayName("注销最后一个会话时删除双 Token 索引并标记用户离线")
    void removesTokenIndexesAndMarksUserOfflineForLastSession() {
        String sessionKey = RedisKeys.userSession(USER_ID, SESSION_ID);
        when(redisUtil.getHash(sessionKey, "accessToken")).thenReturn(Mono.just(OLD_ACCESS_TOKEN));
        when(redisUtil.getHash(sessionKey, "refreshToken")).thenReturn(Mono.just(OLD_REFRESH_TOKEN));
        when(redisUtil.delete(anyString())).thenReturn(Mono.just(true));
        when(redisUtil.removeFromSet(RedisKeys.userSessions(USER_ID), SESSION_ID)).thenReturn(Mono.just(1L));
        when(redisUtil.getSetSize(RedisKeys.userSessions(USER_ID))).thenReturn(Mono.just(0L));
        when(redisUtil.set(RedisKeys.userStatus(USER_ID), "0")).thenReturn(Mono.just(true));

        StepVerifier.create(tokenService.removeSession(USER_ID, SESSION_ID)).verifyComplete();

        verify(redisUtil).delete(RedisKeys.userAccess(OLD_ACCESS_TOKEN));
        verify(redisUtil).delete(RedisKeys.userRefresh(OLD_REFRESH_TOKEN));
        verify(redisUtil).delete(sessionKey);
        verify(redisUtil).set(RedisKeys.userStatus(USER_ID), "0");
        verify(redisUtil).delete(RedisKeys.userSessions(USER_ID));
    }

    @Test
    @DisplayName("注销一个会话后仍有其他会话时保持用户在线")
    void keepsUserOnlineWhenOtherSessionsRemain() {
        String sessionKey = RedisKeys.userSession(USER_ID, SESSION_ID);
        when(redisUtil.getHash(sessionKey, "accessToken")).thenReturn(Mono.just(OLD_ACCESS_TOKEN));
        when(redisUtil.getHash(sessionKey, "refreshToken")).thenReturn(Mono.just(OLD_REFRESH_TOKEN));
        when(redisUtil.delete(anyString())).thenReturn(Mono.just(true));
        when(redisUtil.removeFromSet(RedisKeys.userSessions(USER_ID), SESSION_ID)).thenReturn(Mono.just(1L));
        when(redisUtil.getSetSize(RedisKeys.userSessions(USER_ID))).thenReturn(Mono.just(2L));

        StepVerifier.create(tokenService.removeSession(USER_ID, SESSION_ID)).verifyComplete();

        verify(redisUtil, never()).set(RedisKeys.userStatus(USER_ID), "0");
        verify(redisUtil, never()).delete(RedisKeys.userSessions(USER_ID));
    }

    private void stubLockAcquired() {
        when(distributedLock.tryLock(anyString(), anyLong())).thenReturn(Mono.just(LOCK_VALUE));
        when(distributedLock.unlock(anyString(), anyString())).thenReturn(Mono.just(true));
    }

    private void stubRefreshClaims() {
        when(jwtUtil.extractUserId(OLD_REFRESH_TOKEN)).thenReturn(USER_ID);
        when(jwtUtil.extractSessionId(OLD_REFRESH_TOKEN)).thenReturn(SESSION_ID);
    }

    private void stubStoredSession(String storedRefreshToken) {
        String sessionKey = RedisKeys.userSession(USER_ID, SESSION_ID);
        when(redisUtil.get(RedisKeys.userRefresh(OLD_REFRESH_TOKEN)))
            .thenReturn(Mono.just(USER_ID + ":" + SESSION_ID));
        when(redisUtil.getHash(sessionKey, "refreshToken")).thenReturn(Mono.just(storedRefreshToken));
        when(redisUtil.getHash(sessionKey, "username")).thenReturn(Mono.just("alice"));
        when(redisUtil.getHash(sessionKey, "accessToken")).thenReturn(Mono.just(OLD_ACCESS_TOKEN));
    }

    private void stubSuccessfulWrites() {
        when(redisUtil.delete(anyString())).thenReturn(Mono.just(true));
        when(redisUtil.putHash(anyString(), anyString(), anyString())).thenReturn(Mono.just(true));
        when(redisUtil.set(anyString(), anyString(), anyLong())).thenReturn(Mono.just(true));
        when(redisUtil.set(anyString(), anyString())).thenReturn(Mono.just(true));
        when(redisUtil.expire(anyString(), anyLong())).thenReturn(Mono.just(true));
    }

    private boolean isUnauthorized(Throwable error) {
        return error instanceof BusinessException businessException
            && businessException.getHttpStatus() == HttpCode.UNAUTHORIZED;
    }
}

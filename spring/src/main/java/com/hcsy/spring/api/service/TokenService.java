package com.hcsy.spring.api.service;

import java.util.List;

import com.hcsy.spring.entity.vo.TokenRefreshVO;
import com.hcsy.spring.entity.vo.UserLoginVO;

import reactor.core.publisher.Mono;

public interface TokenService {
    Mono<UserLoginVO> createLoginSession(Long userId, String username);

    Mono<TokenRefreshVO> refreshToken(String refreshToken);

    Mono<Void> removeSessionByAccessToken(String accessToken);

    Mono<Void> removeSession(Long userId, String sessionId);

    Mono<Boolean> validateAccessTokenInRedis(Long userId, String sessionId, String accessToken);

    Mono<Long> getUserOnlineDeviceCount(Long userId);

    Mono<List<String>> getUserSessions(Long userId);

    Mono<Void> forceLogoutUser(Long userId);

    Mono<Integer> removeOtherSessions(Long userId, String currentAccessToken);

    Mono<Void> cleanupExpiredTokens();
}

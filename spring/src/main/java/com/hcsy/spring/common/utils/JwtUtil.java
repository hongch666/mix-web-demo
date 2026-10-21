package com.hcsy.spring.common.utils;

import java.nio.charset.StandardCharsets;
import java.security.Key;
import java.util.Date;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

import org.springframework.stereotype.Component;

import com.hcsy.spring.common.constants.HttpCode;
import com.hcsy.spring.common.constants.Messages;
import com.hcsy.spring.common.exceptions.BusinessException;
import com.hcsy.spring.config.properties.JwtProperties;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.ExpiredJwtException;
import io.jsonwebtoken.JwtException;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.SignatureAlgorithm;
import io.jsonwebtoken.security.Keys;
import jakarta.annotation.PostConstruct;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

/**
 * 封装用户 access token 与 refresh token 的生成、解析、校验及有效期计算
 */
@Component
@RequiredArgsConstructor
@Slf4j
public class JwtUtil {
    private final JwtProperties jwtProperties;
    private final SimpleLogger logger;
    private Key key;

    /**
     * 启动时校验并初始化 JWT 的 HMAC 签名密钥
     */
    @PostConstruct
    public void initKey() {
        if (jwtProperties.secret() == null || jwtProperties.secret().isEmpty()) {
            throw BusinessException.builder().httpStatus(HttpCode.INTERNAL_SERVER_ERROR)
                .errorMessage(Messages.JWT_NOT_NULL).build();
        }
        key = Keys.hmacShaKeyFor(jwtProperties.secret().getBytes(StandardCharsets.UTF_8));
        log.info(Messages.JWT_INIT);
    }

    /**
     * 生成 access token
     */
    public String generateAccessToken(Long userId, String username, String sessionId) {
        Map<String, Object> claims = new HashMap<>();
        claims.put("userId", userId);
        claims.put("username", username);
        claims.put("sessionId", sessionId);
        claims.put("tokenType", "access");

        return Jwts.builder()
            .setClaims(claims)
            .setSubject(username)
            .setIssuedAt(new Date())
            .setExpiration(new Date(System.currentTimeMillis() + jwtProperties.accessExpiration()))
            .signWith(key, SignatureAlgorithm.HS256)
            .compact();
    }

    /**
     * 生成 refresh token
     */
    public String generateRefreshToken(Long userId, String username, String sessionId) {
        Map<String, Object> claims = new HashMap<>();
        claims.put("userId", userId);
        claims.put("username", username);
        claims.put("sessionId", sessionId);
        claims.put("tokenType", "refresh");

        return Jwts.builder()
            .setClaims(claims)
            .setSubject(username)
            .setIssuedAt(new Date())
            .setExpiration(new Date(System.currentTimeMillis() + jwtProperties.refreshExpiration()))
            .signWith(key, SignatureAlgorithm.HS256)
            .compact();
    }

    /**
     * 生成 sessionId
     */
    public String generateSessionId() {
        return UUID.randomUUID().toString();
    }

    /**
     * 从令牌中解析用户名
     */
    public String extractUsername(String token) {
        return getClaims(token).getSubject();
    }

    /**
     * 从令牌中解析用户ID
     */
    public Long extractUserId(String token) {
        return getClaims(token).get("userId", Long.class);
    }

    /**
     * 从令牌中解析会话ID
     */
    public String extractSessionId(String token) {
        return getClaims(token).get("sessionId", String.class);
    }

    /**
     * 从令牌中解析令牌类型（access 或 refresh）
     */
    public String extractTokenType(String token) {
        return getClaims(token).get("tokenType", String.class);
    }

    /**
     * 校验 access token：签名、过期时间、tokenType
     */
    public boolean validateAccessToken(String token) {
        try {
            Claims claims = getClaims(token);
            String tokenType = claims.get("tokenType", String.class);
            if (!"access".equals(tokenType)) {
                logger.warning(Messages.TOKEN_TYPE_INVALID);
                throw BusinessException.builder().httpStatus(HttpCode.UNAUTHORIZED)
                    .errorMessage(Messages.TOKEN_TYPE_INVALID).build();
            }
            logger.debug(Messages.TOKEN_VERIFY_SUCCESS);
            return true;
        } catch (ExpiredJwtException e) {
            logger.warning(Messages.TOKEN_EXPIRED);
            throw BusinessException.builder().httpStatus(HttpCode.UNAUTHORIZED).errorMessage(Messages.TOKEN_EXPIRED)
                .build();
        } catch (BusinessException e) {
            throw e;
        } catch (JwtException | IllegalArgumentException e) {
            logger.warning(Messages.UNUSED_TOKEN + e.getMessage());
            throw BusinessException.builder().httpStatus(HttpCode.UNAUTHORIZED).errorMessage(Messages.UNUSED_TOKEN)
                .build();
        }
    }

    /**
     * 校验 refresh token：签名、过期时间、tokenType
     */
    public boolean validateRefreshToken(String token) {
        try {
            Claims claims = getClaims(token);
            String tokenType = claims.get("tokenType", String.class);
            if (!"refresh".equals(tokenType)) {
                logger.warning(Messages.TOKEN_TYPE_INVALID);
                throw BusinessException.builder().httpStatus(HttpCode.UNAUTHORIZED)
                    .errorMessage(Messages.TOKEN_TYPE_INVALID).build();
            }
            logger.debug(Messages.TOKEN_VERIFY_SUCCESS);
            return true;
        } catch (ExpiredJwtException e) {
            logger.warning(Messages.TOKEN_EXPIRED);
            throw BusinessException.builder().httpStatus(HttpCode.UNAUTHORIZED).errorMessage(Messages.TOKEN_EXPIRED)
                .build();
        } catch (BusinessException e) {
            throw e;
        } catch (JwtException | IllegalArgumentException e) {
            logger.warning(Messages.UNUSED_TOKEN + e.getMessage());
            throw BusinessException.builder().httpStatus(HttpCode.UNAUTHORIZED).errorMessage(Messages.UNUSED_TOKEN)
                .build();
        }
    }

    /**
     * 解析令牌并返回签名校验后的 Claims
     */
    private Claims getClaims(String token) {
        return Jwts.parserBuilder()
            .setSigningKey(key)
            .build()
            .parseClaimsJws(token)
            .getBody();
    }

    /**
     * 返回访问令牌的有效期毫秒数
     */
    public long getAccessExpiration() {
        return jwtProperties.accessExpiration();
    }

    /**
     * 返回刷新令牌的有效期毫秒数
     */
    public long getRefreshExpiration() {
        return jwtProperties.refreshExpiration();
    }

    /**
     * 返回访问令牌的有效期秒数
     */
    public long getAccessExpirationSeconds() {
        return jwtProperties.accessExpiration() / 1000;
    }

    /**
     * 返回刷新令牌的有效期秒数
     */
    public long getRefreshExpirationSeconds() {
        return jwtProperties.refreshExpiration() / 1000;
    }

    /**
     * 返回令牌距离过期的剩余毫秒数
     */
    public long getRemainingTime(String token) {
        Date expiration = getClaims(token).getExpiration();
        return expiration.getTime() - System.currentTimeMillis();
    }

    /**
     * 获取 access token 剩余秒数
     */
    public long getAccessRemainingSeconds(String token) {
        long remainingMs = getRemainingTime(token);
        return remainingMs > 0 ? remainingMs / 1000 : 0;
    }

    /**
     * 获取 refresh token 剩余秒数
     */
    public long getRefreshRemainingSeconds(String token) {
        long remainingMs = getRemainingTime(token);
        return remainingMs > 0 ? remainingMs / 1000 : 0;
    }
}

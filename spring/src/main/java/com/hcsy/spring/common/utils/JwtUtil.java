package com.hcsy.spring.common.utils;

import java.nio.charset.StandardCharsets;
import java.security.Key;
import java.util.Date;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

import org.springframework.stereotype.Component;

import com.hcsy.spring.common.exceptions.BusinessException;
import com.hcsy.spring.core.properties.JwtProperties;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.ExpiredJwtException;
import io.jsonwebtoken.JwtException;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.SignatureAlgorithm;
import io.jsonwebtoken.security.Keys;
import jakarta.annotation.PostConstruct;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

@Component
@RequiredArgsConstructor
@Slf4j
public class JwtUtil {
    private final JwtProperties jwtProperties;
    private final SimpleLogger logger;
    private Key key;

    @PostConstruct
    public void initKey() {
        if (jwtProperties.getSecret() == null || jwtProperties.getSecret().isEmpty()) {
            throw BusinessException.builder().httpStatus(HttpCode.INTERNAL_SERVER_ERROR).errorMessage(Constants.JWT_NOT_NULL).build();
        }
        key = Keys.hmacShaKeyFor(jwtProperties.getSecret().getBytes(StandardCharsets.UTF_8));
        log.info(Constants.JWT_INIT);
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
            .setExpiration(new Date(System.currentTimeMillis() + jwtProperties.getAccessExpiration()))
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
            .setExpiration(new Date(System.currentTimeMillis() + jwtProperties.getRefreshExpiration()))
            .signWith(key, SignatureAlgorithm.HS256)
            .compact();
    }

    /**
     * 生成 sessionId
     */
    public String generateSessionId() {
        return UUID.randomUUID().toString();
    }

    public String extractUsername(String token) {
        return getClaims(token).getSubject();
    }

    public Long extractUserId(String token) {
        return getClaims(token).get("userId", Long.class);
    }

    public String extractSessionId(String token) {
        return getClaims(token).get("sessionId", String.class);
    }

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
                logger.warning(Constants.TOKEN_TYPE_INVALID);
                throw BusinessException.builder().httpStatus(HttpCode.UNAUTHORIZED).errorMessage(Constants.TOKEN_TYPE_INVALID).build();
            }
            logger.debug(Constants.TOKEN_VERIFY_SUCCESS);
            return true;
        } catch (ExpiredJwtException e) {
            logger.warning(Constants.TOKEN_EXPIRED);
            throw BusinessException.builder().httpStatus(HttpCode.UNAUTHORIZED).errorMessage(Constants.TOKEN_EXPIRED).build();
        } catch (BusinessException e) {
            throw e;
        } catch (JwtException | IllegalArgumentException e) {
            logger.warning(Constants.UNUSED_TOKEN + e.getMessage());
            throw BusinessException.builder().httpStatus(HttpCode.UNAUTHORIZED).errorMessage(Constants.UNUSED_TOKEN).build();
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
                logger.warning(Constants.TOKEN_TYPE_INVALID);
                throw BusinessException.builder().httpStatus(HttpCode.UNAUTHORIZED).errorMessage(Constants.TOKEN_TYPE_INVALID).build();
            }
            logger.debug(Constants.TOKEN_VERIFY_SUCCESS);
            return true;
        } catch (ExpiredJwtException e) {
            logger.warning(Constants.TOKEN_EXPIRED);
            throw BusinessException.builder().httpStatus(HttpCode.UNAUTHORIZED).errorMessage(Constants.TOKEN_EXPIRED).build();
        } catch (BusinessException e) {
            throw e;
        } catch (JwtException | IllegalArgumentException e) {
            logger.warning(Constants.UNUSED_TOKEN + e.getMessage());
            throw BusinessException.builder().httpStatus(HttpCode.UNAUTHORIZED).errorMessage(Constants.UNUSED_TOKEN).build();
        }
    }

    private Claims getClaims(String token) {
        return Jwts.parserBuilder()
            .setSigningKey(key)
            .build()
            .parseClaimsJws(token)
            .getBody();
    }

    public long getAccessExpiration() {
        return jwtProperties.getAccessExpiration();
    }

    public long getRefreshExpiration() {
        return jwtProperties.getRefreshExpiration();
    }

    public long getAccessExpirationSeconds() {
        return jwtProperties.getAccessExpiration() / 1000;
    }

    public long getRefreshExpirationSeconds() {
        return jwtProperties.getRefreshExpiration() / 1000;
    }

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

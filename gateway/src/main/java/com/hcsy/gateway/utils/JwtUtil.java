package com.hcsy.gateway.utils;

import java.nio.charset.StandardCharsets;
import java.security.Key;
import java.util.Date;

import org.springframework.stereotype.Component;

import com.hcsy.gateway.common.BusinessException;
import com.hcsy.gateway.common.constants.ErrorCodes;
import com.hcsy.gateway.properties.JwtProperties;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.ExpiredJwtException;
import io.jsonwebtoken.JwtException;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import jakarta.annotation.PostConstruct;

@Component
public class JwtUtil {
    private final JwtProperties jwtProperties;
    private Key key;

    public JwtUtil(JwtProperties jwtProperties) {
        this.jwtProperties = jwtProperties;
        this.initKey();
    }

    @PostConstruct
    public void initKey() {
        if (jwtProperties.getSecret() == null || jwtProperties.getSecret().isEmpty()) {
            throw new IllegalStateException("JWT secret must not be null or empty");
        }
        key = Keys.hmacShaKeyFor(jwtProperties.getSecret().getBytes(StandardCharsets.UTF_8));
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
     * 校验 access token：签名、过期时间、tokenType=access
     */
    public boolean validateAccessToken(String token) {
        try {
            Claims claims = getClaims(token);
            String tokenType = claims.get("tokenType", String.class);
            if (!"access".equals(tokenType)) {
                throw BusinessException.unauthorized("Token类型错误", ErrorCodes.TOKEN_TYPE_INVALID);
            }
            return true;
        } catch (ExpiredJwtException e) {
            throw BusinessException.unauthorized("Token已过期", ErrorCodes.TOKEN_EXPIRED);
        } catch (BusinessException e) {
            throw e;
        } catch (JwtException | IllegalArgumentException e) {
            throw BusinessException.unauthorized("无效的Token", ErrorCodes.TOKEN_INVALID);
        }
    }

    private Claims getClaims(String token) {
        return Jwts.parserBuilder()
                .setSigningKey(key)
                .build()
                .parseClaimsJws(token)
                .getBody();
    }

    public long getRemainingTime(String token) {
        Date expiration = getClaims(token).getExpiration();
        return expiration.getTime() - System.currentTimeMillis();
    }
}

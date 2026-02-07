package com.hcsy.spring.common.utils;

import io.jsonwebtoken.*;
import io.jsonwebtoken.security.Keys;
import jakarta.annotation.PostConstruct;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

import org.springframework.stereotype.Component;

import com.hcsy.spring.common.exceptions.BusinessException;
import com.hcsy.spring.common.properties.InternalTokenProperties;

import java.nio.charset.StandardCharsets;
import java.security.Key;
import java.util.Date;
import java.util.HashMap;
import java.util.Map;

@Component
@RequiredArgsConstructor
@Slf4j
public class InternalTokenUtil {
    private final InternalTokenProperties internalTokenProperties;
    private final SimpleLogger logger;
    private Key key;

    @PostConstruct
    public void initKey() {
        if (internalTokenProperties.getSecret() == null || internalTokenProperties.getSecret().isEmpty()) {
            throw new BusinessException(Constants.INTERNAL_TOKEN_NOT_NULL);
        }
        key = Keys.hmacShaKeyFor(internalTokenProperties.getSecret().getBytes(StandardCharsets.UTF_8));
        log.info(Constants.INTERNAL_TOKEN_INIT);
    }

    /**
     * 生成内部服务令牌（短有效期）
     */
    public String generateInternalToken(Long userId, String serviceName) {
        Map<String, Object> claims = new HashMap<>();
        claims.put("userId", userId);
        claims.put("serviceName", serviceName);
        claims.put("tokenType", "internal");

        return Jwts.builder()
                .setClaims(claims)
                .setSubject("internal_service_token")
                .setIssuedAt(new Date())
                .setExpiration(new Date(System.currentTimeMillis() + internalTokenProperties.getExpiration()))
                .signWith(key, SignatureAlgorithm.HS256)
                .compact();
    }

    /**
     * 验证内部令牌有效性
     */
    public boolean validateInternalToken(String token) {
        try {
            Jwts.parserBuilder()
                    .setSigningKey(key)
                    .build()
                    .parseClaimsJws(token);
            logger.debug(Constants.INTERNAL_TOKEN_VALIDATE_SUCCESS);
            return true;
        } catch (ExpiredJwtException e) {
            logger.warning(Constants.INTERNAL_TOKEN_EXPIRED);
            throw new BusinessException(Constants.INTERNAL_TOKEN_EXPIRED);
        } catch (JwtException | IllegalArgumentException e) {
            logger.warning(Constants.INTERNAL_TOKEN_INVALID + e.getMessage());
            throw new BusinessException(Constants.INTERNAL_TOKEN_INVALID);
        }
    }

    /**
     * 从令牌中提取用户ID
     */
    public Long extractUserId(String token) {
        return getClaims(token).get("userId", Long.class);
    }

    /**
     * 从令牌中提取服务名称
     */
    public String extractServiceName(String token) {
        return getClaims(token).get("serviceName", String.class);
    }

    /**
     * 私有方法：解析令牌获取Claims
     */
    private Claims getClaims(String token) {
        return Jwts.parserBuilder()
                .setSigningKey(key)
                .build()
                .parseClaimsJws(token)
                .getBody();
    }

    /**
     * 获取令牌剩余有效期（毫秒）
     */
    public long getRemainingTime(String token) {
        Date expiration = getClaims(token).getExpiration();
        return expiration.getTime() - System.currentTimeMillis();
    }
}

package com.hcsy.spring.common.utils;

import io.jsonwebtoken.*;
import io.jsonwebtoken.security.Keys;
import jakarta.annotation.PostConstruct;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

import org.springframework.stereotype.Component;

import com.hcsy.spring.common.config.JwtProperties;
import com.hcsy.spring.common.exceptions.BusinessException;

import java.nio.charset.StandardCharsets;
import java.security.Key;
import java.util.Date;
import java.util.HashMap;
import java.util.Map;

@Component
@RequiredArgsConstructor
@Slf4j
public class JwtUtil {
    private final JwtProperties jwtProperties;
    private final SimpleLogger logger;
    private Key key;

    @PostConstruct
    public void initKey() {
        // 增加空值检查
        if (jwtProperties.getSecret() == null || jwtProperties.getSecret().isEmpty()) {
            throw new BusinessException(Constants.JWT_NOT_NULL);
        }
        key = Keys.hmacShaKeyFor(jwtProperties.getSecret().getBytes(StandardCharsets.UTF_8));
        log.info(Constants.JWT_INIT);
    }

    /**
     * 生成包含用户ID和用户名的JWT
     */
    public String generateToken(Long userId, String username) {
        Map<String, Object> claims = new HashMap<>();
        claims.put("userId", userId); // 用户ID
        claims.put("username", username); // 用户名

        return Jwts.builder()
                .setClaims(claims)
                .setSubject(username) // 主题设为用户名
                .setIssuedAt(new Date())
                .setExpiration(new Date(System.currentTimeMillis() + jwtProperties.getExpiration()))
                .signWith(key, SignatureAlgorithm.HS256)
                .compact();
    }

    /**
     * 从Token中提取用户名
     */
    public String extractUsername(String token) {
        return getClaims(token).getSubject();
    }

    /**
     * 从Token中提取用户ID
     */
    public Long extractUserId(String token) {
        return getClaims(token).get("userId", Long.class);
    }

    /**
     * 验证Token有效性
     */
    public boolean validateToken(String token) {
        try {
            Jwts.parserBuilder()
                    .setSigningKey(key)
                    .build()
                    .parseClaimsJws(token);
            logger.debug(Constants.TOKEN_VERIFY_SUCCESS);
            return true;
        } catch (ExpiredJwtException e) {
            logger.warning(Constants.TOKEN_EXPIRED);
            throw new BusinessException(Constants.TOKEN_EXPIRED);
        } catch (JwtException | IllegalArgumentException e) {
            logger.warning(Constants.UNUSED_TOKEN + e.getMessage());
            throw new BusinessException(Constants.UNUSED_TOKEN);
        }
    }

    /**
     * 私有方法：解析Token获取Claims
     */
    private Claims getClaims(String token) {
        return Jwts.parserBuilder()
                .setSigningKey(key)
                .build()
                .parseClaimsJws(token)
                .getBody();
    }

    /**
     * 获取Token剩余有效期（毫秒）
     */
    public long getRemainingTime(String token) {
        Date expiration = getClaims(token).getExpiration();
        return expiration.getTime() - System.currentTimeMillis();
    }
}
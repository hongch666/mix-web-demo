package com.hcsy.spring.utils;

import io.jsonwebtoken.*;
import io.jsonwebtoken.security.Keys;
import jakarta.annotation.PostConstruct;

import org.springframework.stereotype.Component;

import com.hcsy.spring.config.JwtProperties;

import java.nio.charset.StandardCharsets;
import java.security.Key;
import java.util.Date;
import java.util.HashMap;
import java.util.Map;

@Component
public class JwtUtil {
    private static JwtProperties jwtProperties = new JwtProperties();
    private static Key key;

    public JwtUtil(JwtProperties jwtProperties) {
        JwtUtil.jwtProperties = jwtProperties;
    }

    @PostConstruct
    public void initKey() {
        JwtUtil.key = Keys.hmacShaKeyFor(jwtProperties.getSecret().getBytes(StandardCharsets.UTF_8));
    }
    /*
     * // 建议使用 >=32字节的密钥，否则会抛异常
     * private static final String SECRET_KEY = "hcsyhcsyhcsyhcsyhcsyhcsyhcsyhcsy";
     * private static final Key KEY =
     * Keys.hmacShaKeyFor(SECRET_KEY.getBytes(StandardCharsets.UTF_8));
     * private static final long EXPIRATION_TIME = 86400000L; // 1天（毫秒）
     */

    public static String generateToken(String username) {
        Map<String, Object> claims = new HashMap<>();
        claims.put("username", username); // 可扩展更多自定义数据

        return Jwts.builder()
                .setClaims(claims)
                .setSubject(username)
                .setIssuedAt(new Date())
                .setExpiration(new Date(System.currentTimeMillis() + jwtProperties.getExpiration()))
                .signWith(key, SignatureAlgorithm.HS256)
                .compact();
    }

    public String extractUsername(String token) {
        Claims claims = Jwts.parserBuilder()
                .setSigningKey(key)
                .build()
                .parseClaimsJws(token)
                .getBody();
        return claims.getSubject();
    }

    public boolean validateToken(String token) {
        try {
            Jwts.parserBuilder()
                    .setSigningKey(key)
                    .build()
                    .parseClaimsJws(token);
            return true;
        } catch (JwtException | IllegalArgumentException e) {
            return false;
        }
    }
}

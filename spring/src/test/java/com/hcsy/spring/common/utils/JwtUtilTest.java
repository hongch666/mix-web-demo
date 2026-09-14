package com.hcsy.spring.common.utils;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.test.util.ReflectionTestUtils;

import com.hcsy.spring.common.exceptions.BusinessException;
import com.hcsy.spring.core.properties.JwtProperties;

class JwtUtilTest {
    private JwtUtil jwt;

    @BeforeEach
    void setUp() {
        String secret = "01234567890123456789012345678901";
        SimpleLogger logger = new SimpleLogger();
        ReflectionTestUtils.setField(logger, "logPath", "target/test-logs");
        jwt = new JwtUtil(new JwtProperties(secret, 60_000L, 120_000L), logger);
        jwt.initKey();
    }

    @Test
    void generatesAndExtractsAccessTokenClaims() {
        String token = jwt.generateAccessToken(9L, "alice", "session");

        assertEquals("alice", jwt.extractUsername(token));
        assertEquals(9L, jwt.extractUserId(token));
        assertEquals("session", jwt.extractSessionId(token));
        assertEquals("access", jwt.extractTokenType(token));
        assertTrue(jwt.validateAccessToken(token));
        assertTrue(jwt.getAccessRemainingSeconds(token) > 0);
    }

    @Test
    void rejectsRefreshTokenAsAccessToken() {
        String token = jwt.generateRefreshToken(9L, "alice", "session");
        assertTrue(jwt.validateRefreshToken(token));
        assertThrows(BusinessException.class, () -> jwt.validateAccessToken(token));
    }

    @Test
    void rejectsMalformedToken() {
        assertThrows(BusinessException.class, () -> jwt.validateAccessToken("not-a-jwt"));
    }
}

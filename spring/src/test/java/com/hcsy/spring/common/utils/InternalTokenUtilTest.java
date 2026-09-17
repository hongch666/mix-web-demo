package com.hcsy.spring.common.utils;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.Mockito.mock;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import com.hcsy.spring.common.exceptions.BusinessException;
import com.hcsy.spring.core.properties.InternalTokenProperties;

class InternalTokenUtilTest {

    private static final String SECRET = "unit-test-internal-token-secret-32-bytes";
    private InternalTokenUtil tokenUtil;

    @BeforeEach
    void setUp() {
        tokenUtil = createTokenUtil(SECRET);
    }

    @Test
    @DisplayName("生成并解析内部令牌声明")
    void generatesAndExtractsInternalTokenClaims() {
        String token = tokenUtil.generateInternalToken(10001L, "spring");

        assertTrue(tokenUtil.validateInternalToken(token));
        assertEquals(10001L, tokenUtil.extractUserId(token));
        assertEquals("spring", tokenUtil.extractServiceName(token));
        assertTrue(tokenUtil.getRemainingTime(token) > 0);
    }

    @Test
    @DisplayName("拒绝使用其他密钥签名的内部令牌")
    void rejectsTokenSignedWithAnotherSecret() {
        String token = tokenUtil.generateInternalToken(10001L, "spring");
        InternalTokenUtil verifier = createTokenUtil("another-unit-test-secret-with-32-bytes");

        assertThrows(BusinessException.class, () -> verifier.validateInternalToken(token));
    }

    @Test
    @DisplayName("拒绝格式错误的内部令牌")
    void rejectsMalformedToken() {
        assertThrows(BusinessException.class, () -> tokenUtil.validateInternalToken("not-a-jwt"));
    }

    private InternalTokenUtil createTokenUtil(String secret) {
        InternalTokenUtil util = new InternalTokenUtil(
            new InternalTokenProperties(secret, 60_000L),
            mock(SimpleLogger.class));
        util.initKey();
        return util;
    }
}

package com.hcsy.spring.common.utils;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import com.hcsy.spring.common.exceptions.BusinessException;
import com.hcsy.spring.core.properties.InternalTokenProperties;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.Mockito.mock;

class InternalTokenUtilTest {

    private static final String SECRET = "unit-test-internal-token-secret-32-bytes";
    private InternalTokenUtil tokenUtil;

    @BeforeEach
    void setUp() {
        tokenUtil = createTokenUtil(SECRET);
    }

    // 验证该场景的预期行为

    @Test
    @DisplayName("生成并解析内部令牌声明")
    void generatesAndExtractsInternalTokenClaims() {
        InternalTokenUtil configuredTokenUtil = createTokenUtil(resolveConfiguredSecret());
        String token = configuredTokenUtil.generateInternalToken(10001L, "spring");

        System.out.println("生成的内部Token: " + token);

        assertTrue(configuredTokenUtil.validateInternalToken(token));
        assertEquals(10001L, configuredTokenUtil.extractUserId(token));
        assertEquals("spring", configuredTokenUtil.extractServiceName(token));
        assertTrue(configuredTokenUtil.getRemainingTime(token) > 0);
    }

    // 验证该场景的预期行为

    @Test
    @DisplayName("拒绝使用其他密钥签名的内部令牌")
    void rejectsTokenSignedWithAnotherSecret() {
        String token = tokenUtil.generateInternalToken(10001L, "spring");
        InternalTokenUtil verifier = createTokenUtil("another-unit-test-secret-with-32-bytes");

        assertThrows(BusinessException.class, () -> verifier.validateInternalToken(token));
    }

    // 验证该场景的预期行为

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

    private String resolveConfiguredSecret() {
        String environmentSecret = System.getenv("INTERNAL_TOKEN_SECRET");
        if (environmentSecret != null && !environmentSecret.isBlank()) {
            return environmentSecret.trim();
        }

        String systemSecret = System.getProperty("INTERNAL_TOKEN_SECRET");
        if (systemSecret != null && !systemSecret.isBlank()) {
            return systemSecret.trim();
        }

        for (Path candidate : List.of(Path.of(".env"), Path.of("spring/.env"), Path.of("../.env"))) {
            String fileSecret = readSecret(candidate);
            if (fileSecret != null) {
                return fileSecret;
            }
        }
        return SECRET;
    }

    private String readSecret(Path path) {
        if (!Files.exists(path)) {
            return null;
        }
        try {
            return Files.readAllLines(path).stream()
                .map(String::trim)
                .filter(line -> line.startsWith("INTERNAL_TOKEN_SECRET="))
                .map(line -> stripQuotes(line.substring(line.indexOf('=') + 1).trim()))
                .filter(value -> !value.isBlank())
                .findFirst()
                .orElse(null);
        } catch (IOException e) {
            return null;
        }
    }

    private String stripQuotes(String value) {
        if (value.length() >= 2 &&
            ((value.startsWith("\"") && value.endsWith("\"")) ||
                (value.startsWith("'") && value.endsWith("'")))) {
            return value.substring(1, value.length() - 1);
        }
        return value;
    }
}

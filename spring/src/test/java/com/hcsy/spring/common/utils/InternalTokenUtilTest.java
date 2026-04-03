package com.hcsy.spring.common.utils;

import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;

import org.junit.jupiter.api.Assumptions;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import com.hcsy.spring.core.properties.InternalTokenProperties;

import lombok.extern.slf4j.Slf4j;

@Slf4j
class InternalTokenUtilTest {

    private static final String DEFAULT_INTERNAL_TOKEN_SECRET = "abcdefghijklmnopqrstuvwxyz123456";
    private static final long DEFAULT_INTERNAL_TOKEN_EXPIRATION = 60_000L;

    private InternalTokenUtil internalTokenUtil;

    @BeforeEach
    void setUp() {
        InternalTokenProperties internalTokenProperties = new InternalTokenProperties();
        Map<String, String> envValues = loadDotEnvValues();

        internalTokenProperties.setSecret(resolveConfigValue(
                envValues,
                "INTERNAL_TOKEN_SECRET",
                DEFAULT_INTERNAL_TOKEN_SECRET));
        internalTokenProperties.setExpiration(Long.parseLong(resolveConfigValue(
                envValues,
                "INTERNAL_TOKEN_EXPIRATION",
                String.valueOf(DEFAULT_INTERNAL_TOKEN_EXPIRATION))));

        internalTokenUtil = new InternalTokenUtil(internalTokenProperties, new SimpleLogger());
        internalTokenUtil.initKey();
    }

    @Test
    @DisplayName("应该生成可用的内部Token")
    void shouldGenerateInternalToken() {
        String internalToken = internalTokenUtil.generateInternalToken(10001L, "spring");

        assertNotNull(internalToken);
        assertTrue(internalToken.length() > 0);
        log.info("生成的内部Token: {}", internalToken);
    }

    @Test
    @DisplayName("应该使用内部代码和配置校验内部Token")
    void shouldValidateInternalToken() {
        String internalToken = System.getenv("INTERNAL_TOKEN_TEST_TOKEN");
        Assumptions.assumeTrue(Objects.nonNull(internalToken) && !internalToken.isEmpty(),
                "环境变量 INTERNAL_TOKEN_TEST_TOKEN 不能为空");

        assertTrue(internalTokenUtil.validateInternalToken(internalToken));
    }

    private Map<String, String> loadDotEnvValues() {
        Map<String, String> values = new HashMap<>();
        List<Path> candidates = List.of(
                Path.of(".env"),
                Path.of("spring/.env"),
                Path.of("../.env"));

        for (Path candidate : candidates) {
            if (!Files.exists(candidate)) {
                continue;
            }

            try {
                for (String line : Files.readAllLines(candidate)) {
                    String trimmedLine = line.trim();
                    if (trimmedLine.isEmpty() || trimmedLine.startsWith("#") || !trimmedLine.contains("=")) {
                        continue;
                    }

                    String[] parts = trimmedLine.split("=", 2);
                    String key = parts[0].trim();
                    String value = stripQuotes(parts[1].trim());
                    values.put(key, value);
                }
                break;
            } catch (IOException e) {
                throw new IllegalStateException("读取 .env 文件失败: " + candidate, e);
            }
        }

        return values;
    }

    private String resolveConfigValue(Map<String, String> envValues, String key, String defaultValue) {
        String systemValue = System.getenv(key);
        if (systemValue != null && !systemValue.isBlank()) {
            return systemValue.trim();
        }

        String dotEnvValue = envValues.get(key);
        if (dotEnvValue != null && !dotEnvValue.isBlank()) {
            return dotEnvValue.trim();
        }

        return defaultValue;
    }

    private String stripQuotes(String value) {
        if (value.length() >= 2) {
            char first = value.charAt(0);
            char last = value.charAt(value.length() - 1);
            if ((first == '"' && last == '"') || (first == '\'' && last == '\'')) {
                return value.substring(1, value.length() - 1);
            }
        }
        return value;
    }
}

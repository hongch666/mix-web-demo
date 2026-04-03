package com.hcsy.spring.common.utils;

import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.Objects;

import org.junit.jupiter.api.Assumptions;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import com.hcsy.spring.core.properties.InternalTokenProperties;

import lombok.extern.slf4j.Slf4j;

@Slf4j
class InternalTokenUtilTest {

    private InternalTokenUtil internalTokenUtil;

    @BeforeEach
    void setUp() {
        InternalTokenProperties internalTokenProperties = new InternalTokenProperties();
        internalTokenProperties.setSecret("abcdefghijklmnopqrstuvwxyz123456");
        internalTokenProperties.setExpiration(60_000L);

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
}

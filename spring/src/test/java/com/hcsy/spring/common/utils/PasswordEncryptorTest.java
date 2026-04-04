package com.hcsy.spring.common.utils;

import static org.junit.jupiter.api.Assertions.assertTrue;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import lombok.extern.slf4j.Slf4j;

@Slf4j
class PasswordEncryptorTest {

    private static final String RAW_PASSWORD = "123456";
    private static final String ENCODED_PASSWORD = "$2a$10$6YU.1pYb5mfPxQJolVOnOegqYE9KsohbOST/SDCdwNxZ0HpS70t2u";

    private final PasswordEncryptor passwordEncryptor = new PasswordEncryptor();

    @Test
    @DisplayName("应该输出写死明文密码的加密结果")
    void shouldPrintEncodedPassword() {
        String encodedPassword = passwordEncryptor.encryptPassword(RAW_PASSWORD);
        log.info("明文密码加密结果: {}", encodedPassword);
        assertTrue(encodedPassword != null && !encodedPassword.isBlank());
    }

    @Test
    @DisplayName("应该校验写死的密文密码和明文密码匹配")
    void shouldMatchEncodedPassword() {
        boolean matched = passwordEncryptor.matchPassword(RAW_PASSWORD, ENCODED_PASSWORD);
        assertTrue(matched, "写死的密文密码和明文密码不匹配");
    }
}

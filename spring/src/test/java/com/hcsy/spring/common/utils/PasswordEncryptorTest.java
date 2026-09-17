package com.hcsy.spring.common.utils;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

class PasswordEncryptorTest {

    private static final String RAW_PASSWORD = "123456";
    private static final String WRONG_PASSWORD = "654321";

    private final PasswordEncryptor passwordEncryptor = new PasswordEncryptor();

    @Test
    @DisplayName("应该先生成密文再使用同一明文校验通过")
    void shouldEncryptThenMatchPassword() {
        // 先生成密文再校验，避免依赖写死的密文结果
        String encodedPassword = passwordEncryptor.encryptPassword(RAW_PASSWORD);

        System.out.println("明文密码加密结果: " + encodedPassword);

        assertNotNull(encodedPassword);
        assertTrue(encodedPassword.length() > 0);
        assertTrue(passwordEncryptor.matchPassword(RAW_PASSWORD, encodedPassword));
    }

    @Test
    @DisplayName("错误明文密码应该校验失败")
    void shouldRejectWrongPassword() {
        String encodedPassword = passwordEncryptor.encryptPassword(RAW_PASSWORD);

        assertFalse(passwordEncryptor.matchPassword(WRONG_PASSWORD, encodedPassword));
    }
}

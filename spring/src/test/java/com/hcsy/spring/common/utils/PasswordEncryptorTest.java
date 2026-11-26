package com.hcsy.spring.common.utils;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;

import com.hcsy.spring.common.constants.HttpCode;
import com.hcsy.spring.common.constants.Messages;
import com.hcsy.spring.common.exceptions.BusinessException;

class PasswordEncryptorTest {
    private static final String RAW_PASSWORD = "abc";
    private static final String RAW_SHA256 = "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad";
    private static final String WRONG_PASSWORD = "def";

    private final PasswordEncryptor passwordEncryptor = new PasswordEncryptor(new BCryptPasswordEncoder());

    @Test
    @DisplayName("应该先生成密文再使用同一摘要校验通过")
    void shouldEncryptThenMatchPassword() {
        String encodedPassword = passwordEncryptor.encryptPassword(RAW_SHA256);

        assertNotNull(encodedPassword);
        assertTrue(encodedPassword.length() > 0);
        assertTrue(passwordEncryptor.matchPassword(RAW_SHA256, encodedPassword));
    }

    @Test
    @DisplayName("错误摘要应该校验失败")
    void shouldRejectWrongPassword() {
        String encodedPassword = passwordEncryptor.encryptPassword(RAW_SHA256);

        assertFalse(passwordEncryptor.matchPassword(passwordEncryptor.hashPassword(WRONG_PASSWORD), encodedPassword));
    }

    @Test
    @DisplayName("服务端明文密码应计算为SHA256摘要")
    void shouldHashRawPassword() {
        assertEquals(RAW_SHA256, passwordEncryptor.hashPassword(RAW_PASSWORD));
    }

    @Test
    @DisplayName("合法的SHA256摘要应原样返回")
    void shouldAcceptSha256Digest() {
        assertEquals(RAW_SHA256, passwordEncryptor.requireSha256Digest(RAW_SHA256));
        assertEquals(RAW_SHA256.toUpperCase(), passwordEncryptor.requireSha256Digest(RAW_SHA256.toUpperCase()));
    }

    @Test
    @DisplayName("非摘要格式的密码应抛出400业务异常")
    void shouldRejectNonDigest() {
        BusinessException error = assertThrows(BusinessException.class,
            () -> passwordEncryptor.requireSha256Digest(RAW_PASSWORD));

        assertEquals(HttpCode.BAD_REQUEST, error.getHttpStatus());
        assertEquals(Messages.PASSWORD_DIGEST_INVALID, error.getErrorMessage());
        assertThrows(BusinessException.class, () -> passwordEncryptor.requireSha256Digest(null));
    }
}

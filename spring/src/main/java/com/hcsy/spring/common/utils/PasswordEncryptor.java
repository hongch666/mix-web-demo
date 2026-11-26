package com.hcsy.spring.common.utils;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;

import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.stereotype.Component;

import com.hcsy.spring.common.constants.Defaults;
import com.hcsy.spring.common.constants.HttpCode;
import com.hcsy.spring.common.constants.Messages;
import com.hcsy.spring.common.exceptions.BusinessException;

import lombok.RequiredArgsConstructor;

/**
 * 密码加密工具类，负责校验前端密码摘要、计算摘要与 BCrypt 加盐哈希
 */
@Component
@RequiredArgsConstructor
public class PasswordEncryptor {
    private final BCryptPasswordEncoder bCryptPasswordEncoder;

    /**
     * 加密密码
     *
     * @param rawPassword
     *                        原始密码
     * @return 加密后的密码
     */
    public String encryptPassword(String rawPassword) {
        return bCryptPasswordEncoder.encode(rawPassword);
    }

    /**
     * 校验前端提交的密码必须是 64 位十六进制 SHA256 摘要，格式不符时抛出 400 业务异常
     */
    public String requireSha256Digest(String password) {
        if (password == null || !password.matches(Defaults.SHA256_PATTERN)) {
            throw new BusinessException(HttpCode.BAD_REQUEST, Messages.PASSWORD_DIGEST_INVALID);
        }
        return password;
    }

    /**
     * 计算服务端配置的明文密码的 SHA256 十六进制摘要
     */
    public String hashPassword(String rawPassword) {
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            return HexFormat.of().formatHex(digest.digest(rawPassword.getBytes(StandardCharsets.UTF_8)));
        } catch (NoSuchAlgorithmException error) {
            throw new BusinessException(HttpCode.INTERNAL_SERVER_ERROR, Messages.PASSWORD_HASH_FAILED, error);
        }
    }

    /**
     * 验证密码是否正确
     *
     * @param rawPassword
     *                            原始密码（用户输入）
     * @param encodedPassword
     *                            数据库中的加密密码
     * @return 是否匹配
     */
    public boolean matchPassword(String rawPassword, String encodedPassword) {
        return bCryptPasswordEncoder.matches(rawPassword, encodedPassword);
    }

    /**
     * 隐藏密码（返回给前端用）
     *
     * @return 隐藏后的密码
     */
    public static String maskPassword() {
        return Defaults.HIDE_PASSWORD;
    }
}

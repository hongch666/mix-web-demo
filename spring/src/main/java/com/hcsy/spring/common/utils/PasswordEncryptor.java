package com.hcsy.spring.common.utils;

import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.stereotype.Component;

/**
 * 密码加密工具类
 */
@Component
public class PasswordEncryptor {

    private final BCryptPasswordEncoder bCryptPasswordEncoder = new BCryptPasswordEncoder();

    /**
     * 加密密码
     * 
     * @param rawPassword 原始密码
     * @return 加密后的密码
     */
    public String encryptPassword(String rawPassword) {
        return bCryptPasswordEncoder.encode(rawPassword);
    }

    /**
     * 验证密码是否正确
     * 
     * @param rawPassword     原始密码（用户输入）
     * @param encodedPassword 数据库中的加密密码
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
        return Constants.HIDE_PASSWORD;
    }
}

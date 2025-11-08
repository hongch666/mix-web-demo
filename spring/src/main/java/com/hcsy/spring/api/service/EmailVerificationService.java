package com.hcsy.spring.api.service;

/**
 * 邮箱验证服务接口
 */
public interface EmailVerificationService {

    /**
     * 发送邮箱验证码
     * 
     * @param email 目标邮箱
     * @return 是否发送成功
     */
    boolean sendVerificationCode(String email);

    /**
     * 验证邮箱验证码
     * 
     * @param email 邮箱地址
     * @param code  验证码
     * @return 是否验证成功
     */
    boolean verifyCode(String email, String code);

    /**
     * 检查邮箱验证状态
     * 
     * @param email 邮箱地址
     * @return 是否已验证
     */
    boolean isEmailVerified(String email);

    /**
     * 标记邮箱已验证
     * 
     * @param email 邮箱地址
     */
    void markEmailAsVerified(String email);
}

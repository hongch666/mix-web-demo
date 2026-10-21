package com.hcsy.spring.application.service;

import reactor.core.publisher.Mono;

/**
 * 邮箱验证码业务接口，定义验证码发送、校验、验证状态查询与标记邮箱已验证的操作
 */
public interface EmailVerificationService {
    /**
     * 生成验证码存入Redis并通过邮件服务发送
     */
    Mono<Void> sendVerificationCode(String email, String type);

    /**
     * 校验邮箱验证码，正确则删除防重放并返回 true
     */
    Mono<Boolean> verifyCode(String email, String code);

    /**
     * 查询邮箱是否已通过验证
     */
    Mono<Boolean> isEmailVerified(String email);

    /**
     * 将邮箱标记为已验证并保留24小时
     */
    Mono<Void> markEmailAsVerified(String email);
}

package com.hcsy.spring.api.service.impl;

import java.util.Random;

import org.springframework.stereotype.Service;

import com.hcsy.spring.api.service.EmailVerificationService;
import com.hcsy.spring.common.utils.Constants;
import com.hcsy.spring.common.utils.RedisUtil;
import com.hcsy.spring.common.utils.Result;
import com.hcsy.spring.common.utils.SimpleLogger;
import com.hcsy.spring.entity.dto.InternalEmailCodeSendDTO;
import com.hcsy.spring.infra.client.NestjsClient;

import lombok.RequiredArgsConstructor;

/**
 * 邮箱验证服务实现
 * 验证码生成和Redis存储由本服务负责，邮件发送委托给 NestJS 邮件服务
 */
@Service
@RequiredArgsConstructor
public class EmailVerificationServiceImpl implements EmailVerificationService {

    private final RedisUtil redisUtil;
    private final SimpleLogger logger;
    private final NestjsClient nestjsClient;

    private static final String VERIFICATION_CODE_PREFIX = "email:verify:";
    private static final long VERIFICATION_CODE_EXPIRY = 10 * 60; // 10分钟过期（秒）

    /**
     * 生成验证码（6位数字）
     */
    private String generateVerificationCode() {
        Random random = new Random();
        return String.format("%06d", random.nextInt(1000000));
    }

    /**
     * 发送邮箱验证码
     *
     * @param email 目标邮箱
     * @param type  验证码场景（register/login/reset）
     */
    @Override
    public void sendVerificationCode(String email, String type) {
        // 生成验证码
        String code = generateVerificationCode();

        // 保存到 Redis（设置过期时间）
        String key = VERIFICATION_CODE_PREFIX + email;
        redisUtil.set(key, code, VERIFICATION_CODE_EXPIRY);
        logger.info(Constants.CODE_SAVE + email);

        // 调用 NestJS 发送邮件
        try {
            Result result = nestjsClient.sendEmailCode(new InternalEmailCodeSendDTO(
                    email,
                    code,
                    type,
                    10));
            if (result.getCode() != 200) {
                throw new RuntimeException(Constants.NESTJS_EMAIL_RESPONSE_FAIL + result.getMsg());
            }
            logger.info(Constants.CODE_SUCCESS + email);
        } catch (Exception e) {
            logger.error(Constants.NESTJS_EMAIL_SEND_FAIL + e.getMessage(), e);
            handleSendFailure(email);
            throw new RuntimeException(Constants.NESTJS_EMAIL_SEND_FAILED_MSG);
        }
    }

    /**
     * 处理发送失败，删除 Redis 中的验证码
     */
    private void handleSendFailure(String email) {
        String key = VERIFICATION_CODE_PREFIX + email;
        redisUtil.delete(key);
        logger.debug(Constants.CODE_DELETE + email);
    }

    /**
     * 验证邮箱验证码
     *
     * @param email 邮箱地址
     * @param code  验证码
     * @return 是否验证成功
     */
    @Override
    public boolean verifyCode(String email, String code) {
        try {
            String key = VERIFICATION_CODE_PREFIX + email;
            String storedCode = redisUtil.get(key);

            if (storedCode == null) {
                logger.info(Constants.CODE_EXPIRED + email);
                return false;
            }

            if (!storedCode.equals(code)) {
                logger.info(Constants.CODE_VERIFY_FAIL + email);
                return false;
            }

            // 验证成功，删除验证码
            redisUtil.delete(key);
            logger.info(Constants.CODE_VERIFY_SUCCESS + email);
            return true;
        } catch (Exception e) {
            logger.error(Constants.CODE_VERIFY_EXCEPTION + e.getMessage(), e);
            return false;
        }
    }

    /**
     * 检查邮箱验证状态
     *
     * @param email 邮箱地址
     * @return 是否已验证
     */
    @Override
    public boolean isEmailVerified(String email) {
        String key = VERIFICATION_CODE_PREFIX + "verified:" + email;
        return redisUtil.get(key) != null;
    }

    /**
     * 标记邮箱已验证
     *
     * @param email 邮箱地址
     */
    @Override
    public void markEmailAsVerified(String email) {
        String key = VERIFICATION_CODE_PREFIX + "verified:" + email;
        redisUtil.set(key, "true", 24 * 60 * 60); // 24小时
    }
}

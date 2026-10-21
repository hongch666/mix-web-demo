package com.hcsy.spring.application.service.impl;

import java.security.SecureRandom;

import org.springframework.stereotype.Service;

import com.hcsy.spring.application.service.EmailVerificationService;
import com.hcsy.spring.common.constants.Messages;
import com.hcsy.spring.common.constants.RedisKeys;
import com.hcsy.spring.common.utils.RedisUtil;
import com.hcsy.spring.common.utils.SimpleLogger;
import com.hcsy.spring.entity.dto.InternalEmailCodeSendDTO;
import com.hcsy.spring.infra.client.NestjsClient;

import lombok.RequiredArgsConstructor;
import reactor.core.publisher.Mono;

/**
 * EmailVerificationService 的实现，生成6位验证码存入Redis（10分钟有效）并调用 NestJS 邮件服务发送，校验通过后立即删除防重放
 */
@Service
@RequiredArgsConstructor
public class EmailVerificationServiceImpl implements EmailVerificationService {

    private static final long VERIFICATION_CODE_EXPIRY = 10 * 60;
    private static final SecureRandom RANDOM = new SecureRandom();

    private final RedisUtil redisUtil;
    private final SimpleLogger logger;
    private final NestjsClient nestjsClient;

    /**
     * 实现生成6位验证码存入Redis（10分钟有效）并调用邮件服务发送
     */
    @Override
    public Mono<Void> sendVerificationCode(String email, String type) {
        String code = String.format("%06d", RANDOM.nextInt(1_000_000));
        String key = RedisKeys.emailVerify(email);
        return redisUtil.set(key, code, VERIFICATION_CODE_EXPIRY)
            .doOnSuccess(ignored -> logger.info(Messages.CODE_SAVE + email))
            .then(nestjsClient.sendEmailCode(new InternalEmailCodeSendDTO(email, code, type, 10)))
            .doOnSuccess(ignored -> logger.info(Messages.CODE_SUCCESS + email))
            .then();
    }

    /**
     * 实现校验邮箱验证码，正确后立即删除防重放，过期或出错返回 false
     */
    @Override
    public Mono<Boolean> verifyCode(String email, String code) {
        String key = RedisKeys.emailVerify(email);
        return redisUtil.get(key)
            .flatMap(storedCode -> {
                if (!storedCode.equals(code)) {
                    logger.info(Messages.CODE_VERIFY_FAIL + email);
                    return Mono.just(false);
                }
                return redisUtil.delete(key)
                    .doOnSuccess(ignored -> logger.info(Messages.CODE_VERIFY_SUCCESS + email))
                    .thenReturn(true);
            })
            .switchIfEmpty(Mono.fromSupplier(() -> {
                logger.info(Messages.CODE_EXPIRED + email);
                return false;
            }))
            .onErrorResume(error -> {
                logger.error(Messages.CODE_VERIFY_EXCEPTION + error.getMessage(), error);
                return Mono.just(false);
            });
    }

    /**
     * 实现查询邮箱是否已通过验证
     */
    @Override
    public Mono<Boolean> isEmailVerified(String email) {
        return redisUtil.exists(RedisKeys.emailVerified(email));
    }

    /**
     * 实现将邮箱标记为已验证并保留24小时
     */
    @Override
    public Mono<Void> markEmailAsVerified(String email) {
        return redisUtil.set(RedisKeys.emailVerified(email), "true", 24 * 60 * 60).then();
    }
}

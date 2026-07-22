package com.hcsy.spring.api.service.impl;

import java.security.SecureRandom;

import org.springframework.stereotype.Service;

import com.hcsy.spring.api.service.EmailVerificationService;
import com.hcsy.spring.common.constants.Messages;
import com.hcsy.spring.common.utils.RedisUtil;
import com.hcsy.spring.common.utils.SimpleLogger;
import com.hcsy.spring.entity.dto.InternalEmailCodeSendDTO;
import com.hcsy.spring.infra.client.NestjsClient;

import lombok.RequiredArgsConstructor;
import reactor.core.publisher.Mono;

@Service
@RequiredArgsConstructor
public class EmailVerificationServiceImpl implements EmailVerificationService {

    private static final String VERIFICATION_CODE_PREFIX = "email:verify:";
    private static final long VERIFICATION_CODE_EXPIRY = 10 * 60;
    private static final SecureRandom RANDOM = new SecureRandom();

    private final RedisUtil redisUtil;
    private final SimpleLogger logger;
    private final NestjsClient nestjsClient;

    @Override
    public Mono<Void> sendVerificationCode(String email, String type) {
        String code = String.format("%06d", RANDOM.nextInt(1_000_000));
        String key = VERIFICATION_CODE_PREFIX + email;
        return redisUtil.set(key, code, VERIFICATION_CODE_EXPIRY)
                .doOnSuccess(ignored -> logger.info(Messages.CODE_SAVE + email))
                .then(nestjsClient.sendEmailCode(new InternalEmailCodeSendDTO(email, code, type, 10)))
                .doOnSuccess(ignored -> logger.info(Messages.CODE_SUCCESS + email))
                .then();
    }

    @Override
    public Mono<Boolean> verifyCode(String email, String code) {
        String key = VERIFICATION_CODE_PREFIX + email;
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

    @Override
    public Mono<Boolean> isEmailVerified(String email) {
        return redisUtil.exists(VERIFICATION_CODE_PREFIX + "verified:" + email);
    }

    @Override
    public Mono<Void> markEmailAsVerified(String email) {
        return redisUtil.set(VERIFICATION_CODE_PREFIX + "verified:" + email, "true", 24 * 60 * 60).then();
    }
}

package com.hcsy.spring.api.service;

import reactor.core.publisher.Mono;

public interface EmailVerificationService {
    Mono<Void> sendVerificationCode(String email, String type);

    Mono<Boolean> verifyCode(String email, String code);

    Mono<Boolean> isEmailVerified(String email);

    Mono<Void> markEmailAsVerified(String email);
}

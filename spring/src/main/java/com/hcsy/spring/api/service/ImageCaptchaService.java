package com.hcsy.spring.api.service;

import com.hcsy.spring.entity.vo.ImageCaptchaVO;

import reactor.core.publisher.Mono;

public interface ImageCaptchaService {
    Mono<ImageCaptchaVO> createCaptcha();

    Mono<Boolean> verifyCaptcha(String captchaId, String captchaText);

    Mono<Void> deleteCaptcha(String captchaId);
}

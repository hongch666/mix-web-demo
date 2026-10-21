package com.hcsy.spring.application.service;

import com.hcsy.spring.entity.vo.ImageCaptchaVO;

import reactor.core.publisher.Mono;

/**
 * 图形验证码业务接口，定义验证码的生成、校验与删除操作
 */
public interface ImageCaptchaService {
    /**
     * 生成图形验证码并缓存，返回ID与Base64图片
     */
    Mono<ImageCaptchaVO> createCaptcha();

    /**
     * 校验图形验证码，忽略大小写，过期或不存在返回 false
     */
    Mono<Boolean> verifyCaptcha(String captchaId, String captchaText);

    /**
     * 删除已使用的图形验证码缓存
     */
    Mono<Void> deleteCaptcha(String captchaId);
}

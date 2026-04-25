package com.hcsy.spring.api.service;

import com.hcsy.spring.entity.vo.ImageCaptchaVO;

/**
 * 图形验证码服务
 */
public interface ImageCaptchaService {

    /**
     * 生成图形验证码
     *
     * @return 图形验证码内容
     */
    ImageCaptchaVO createCaptcha();

    /**
     * 校验图形验证码
     *
     * @param captchaId   验证码ID
     * @param captchaText 验证码文本
     * @return 是否校验通过
     */
    boolean verifyCaptcha(String captchaId, String captchaText);

    /**
     * 删除图形验证码
     *
     * @param captchaId 验证码ID
     */
    void deleteCaptcha(String captchaId);
}

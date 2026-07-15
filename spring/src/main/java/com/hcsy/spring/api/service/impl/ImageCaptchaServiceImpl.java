package com.hcsy.spring.api.service.impl;

import java.util.UUID;

import org.springframework.stereotype.Service;

import com.hcsy.spring.api.service.ImageCaptchaService;
import com.hcsy.spring.common.constants.Messages;
import com.hcsy.spring.common.utils.RedisUtil;
import com.hcsy.spring.common.utils.SimpleLogger;
import com.hcsy.spring.entity.vo.ImageCaptchaVO;
import com.wf.captcha.SpecCaptcha;
import com.wf.captcha.base.Captcha;

import lombok.RequiredArgsConstructor;

/**
 * 图形验证码服务实现（基于 EasyCaptcha）
 */
@Service
@RequiredArgsConstructor
public class ImageCaptchaServiceImpl implements ImageCaptchaService {
    private static final String CAPTCHA_PREFIX = "image:captcha:";
    private static final long CAPTCHA_EXPIRY = 5 * 60;
    private static final int CAPTCHA_WIDTH = 130;
    private static final int CAPTCHA_HEIGHT = 40;
    private static final int CAPTCHA_LENGTH = 4;

    private final RedisUtil redisUtil;
    private final SimpleLogger logger;

    @Override
    public ImageCaptchaVO createCaptcha() {
        String captchaId = UUID.randomUUID().toString().replace("-", "");
        String key = buildCaptchaKey(captchaId);

        // 生成 png 格式验证码（如需 GIF 动图改为 new GifCaptcha(...)）
        SpecCaptcha captcha = new SpecCaptcha(CAPTCHA_WIDTH, CAPTCHA_HEIGHT, CAPTCHA_LENGTH);
        captcha.setCharType(Captcha.TYPE_DEFAULT);
        String captchaText = captcha.text();

        redisUtil.set(key, captchaText, CAPTCHA_EXPIRY);
        logger.info(Messages.IMAGE_CAPTCHA_SAVE + captchaId);

        return ImageCaptchaVO.builder()
                .captchaId(captchaId)
                .imageBase64(captcha.toBase64())
                .build();
    }

    @Override
    public boolean verifyCaptcha(String captchaId, String captchaText) {
        String storedCaptcha = redisUtil.get(buildCaptchaKey(captchaId));
        if (storedCaptcha == null || captchaText == null) {
            logger.info(Messages.IMAGE_CAPTCHA_EXPIRED + captchaId);
            return false;
        }

        boolean matched = storedCaptcha.equalsIgnoreCase(captchaText.trim());
        if (!matched) {
            logger.info(Messages.IMAGE_CAPTCHA_VERIFY_FAIL + captchaId);
            return false;
        }

        logger.info(Messages.IMAGE_CAPTCHA_VERIFY_SUCCESS + captchaId);
        return true;
    }

    @Override
    public void deleteCaptcha(String captchaId) {
        redisUtil.delete(buildCaptchaKey(captchaId));
        logger.info(Messages.IMAGE_CAPTCHA_DELETE + captchaId);
    }

    private String buildCaptchaKey(String captchaId) {
        return CAPTCHA_PREFIX + captchaId;
    }
}

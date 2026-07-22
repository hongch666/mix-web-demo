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
import reactor.core.publisher.Mono;
import reactor.core.scheduler.Schedulers;

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
    public Mono<ImageCaptchaVO> createCaptcha() {
        return Mono.fromCallable(this::generateCaptcha)
                .subscribeOn(Schedulers.boundedElastic())
                .flatMap(generated -> redisUtil.set(generated.key(), generated.text(), CAPTCHA_EXPIRY)
                        .doOnSuccess(ignored -> logger.info(Messages.IMAGE_CAPTCHA_SAVE + generated.id()))
                        .thenReturn(generated.vo()));
    }

    @Override
    public Mono<Boolean> verifyCaptcha(String captchaId, String captchaText) {
        return redisUtil.get(buildCaptchaKey(captchaId))
                .map(stored -> captchaText != null && stored.equalsIgnoreCase(captchaText.trim()))
                .doOnNext(matched -> logger.info((matched
                        ? Messages.IMAGE_CAPTCHA_VERIFY_SUCCESS
                        : Messages.IMAGE_CAPTCHA_VERIFY_FAIL) + captchaId))
                .switchIfEmpty(Mono.fromSupplier(() -> {
                    logger.info(Messages.IMAGE_CAPTCHA_EXPIRED + captchaId);
                    return false;
                }));
    }

    @Override
    public Mono<Void> deleteCaptcha(String captchaId) {
        return redisUtil.delete(buildCaptchaKey(captchaId))
                .doOnSuccess(ignored -> logger.info(Messages.IMAGE_CAPTCHA_DELETE + captchaId))
                .then();
    }

    private GeneratedCaptcha generateCaptcha() {
        String captchaId = UUID.randomUUID().toString().replace("-", "");
        SpecCaptcha captcha = new SpecCaptcha(CAPTCHA_WIDTH, CAPTCHA_HEIGHT, CAPTCHA_LENGTH);
        captcha.setCharType(Captcha.TYPE_DEFAULT);
        String text = captcha.text();
        ImageCaptchaVO vo = ImageCaptchaVO.builder()
                .captchaId(captchaId)
                .imageBase64(captcha.toBase64())
                .build();
        return new GeneratedCaptcha(captchaId, buildCaptchaKey(captchaId), text, vo);
    }

    private String buildCaptchaKey(String captchaId) {
        return CAPTCHA_PREFIX + captchaId;
    }

    private record GeneratedCaptcha(String id, String key, String text, ImageCaptchaVO vo) { }
}

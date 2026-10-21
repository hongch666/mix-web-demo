package com.hcsy.spring.application.service.impl;

import java.util.UUID;

import org.springframework.stereotype.Service;

import com.hcsy.spring.application.service.ImageCaptchaService;
import com.hcsy.spring.common.constants.Messages;
import com.hcsy.spring.common.constants.RedisKeys;
import com.hcsy.spring.common.utils.RedisUtil;
import com.hcsy.spring.common.utils.SimpleLogger;
import com.hcsy.spring.entity.vo.ImageCaptchaVO;

import com.wf.captcha.SpecCaptcha;
import com.wf.captcha.base.Captcha;
import lombok.RequiredArgsConstructor;
import reactor.core.publisher.Mono;
import reactor.core.scheduler.Schedulers;

/**
 * ImageCaptchaService 的实现，在 boundedElastic 线程池生成图形验证码写入Redis（5分钟有效），校验时忽略大小写
 */
@Service
@RequiredArgsConstructor
public class ImageCaptchaServiceImpl implements ImageCaptchaService {
    private static final long CAPTCHA_EXPIRY = 5 * 60;
    private static final int CAPTCHA_WIDTH = 130;
    private static final int CAPTCHA_HEIGHT = 40;
    private static final int CAPTCHA_LENGTH = 4;

    private final RedisUtil redisUtil;
    private final SimpleLogger logger;

    /**
     * 实现生成图形验证码写入Redis（5分钟有效）并返回ID与Base64图片
     */
    @Override
    public Mono<ImageCaptchaVO> createCaptcha() {
        return Mono.fromCallable(this::generateCaptcha)
            .subscribeOn(Schedulers.boundedElastic())
            .flatMap(generated -> redisUtil.set(generated.key(), generated.text(), CAPTCHA_EXPIRY)
                .doOnSuccess(ignored -> logger.info(Messages.IMAGE_CAPTCHA_SAVE + generated.id()))
                .thenReturn(generated.vo()));
    }

    /**
     * 实现校验图形验证码，忽略大小写，过期或不存在返回 false
     */
    @Override
    public Mono<Boolean> verifyCaptcha(String captchaId, String captchaText) {
        return redisUtil.get(RedisKeys.imageCaptcha(captchaId))
            .map(stored -> captchaText != null && stored.equalsIgnoreCase(captchaText.trim()))
            .doOnNext(matched -> logger.info((matched
                ? Messages.IMAGE_CAPTCHA_VERIFY_SUCCESS
                : Messages.IMAGE_CAPTCHA_VERIFY_FAIL) + captchaId))
            .switchIfEmpty(Mono.fromSupplier(() -> {
                logger.info(Messages.IMAGE_CAPTCHA_EXPIRED + captchaId);
                return false;
            }));
    }

    /**
     * 实现删除已使用的图形验证码缓存
     */
    @Override
    public Mono<Void> deleteCaptcha(String captchaId) {
        return redisUtil.delete(RedisKeys.imageCaptcha(captchaId))
            .doOnSuccess(ignored -> logger.info(Messages.IMAGE_CAPTCHA_DELETE + captchaId))
            .then();
    }

    /**
     * 生成随机ID的图形验证码及其Redis键与Base64图片
     */
    private GeneratedCaptcha generateCaptcha() {
        String captchaId = UUID.randomUUID().toString().replace("-", "");
        SpecCaptcha captcha = new SpecCaptcha(CAPTCHA_WIDTH, CAPTCHA_HEIGHT, CAPTCHA_LENGTH);
        captcha.setCharType(Captcha.TYPE_DEFAULT);
        String text = captcha.text();
        ImageCaptchaVO vo = ImageCaptchaVO.builder()
            .captchaId(captchaId)
            .imageBase64(captcha.toBase64())
            .build();
        return new GeneratedCaptcha(captchaId, RedisKeys.imageCaptcha(captchaId), text, vo);
    }

    /**
     * 承载一次生成的验证码ID、Redis键、明文与视图对象
     */
    private record GeneratedCaptcha(String id, String key, String text, ImageCaptchaVO vo) {
    }
}

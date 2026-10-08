package com.hcsy.spring.api.service.impl;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import com.hcsy.spring.common.constants.RedisKeys;
import com.hcsy.spring.common.utils.RedisUtil;
import com.hcsy.spring.common.utils.SimpleLogger;

import reactor.core.publisher.Mono;
import reactor.test.StepVerifier;

@ExtendWith(MockitoExtension.class)
class ImageCaptchaServiceImplTest {

    private static final String CAPTCHA_ID = "abc123";
    private static final long CAPTCHA_TTL_SECONDS = 5 * 60;

    @Mock
    private RedisUtil redisUtil;
    @Mock
    private SimpleLogger logger;

    private ImageCaptchaServiceImpl imageCaptchaService;

    @BeforeEach
    void setUp() {
        imageCaptchaService = new ImageCaptchaServiceImpl(redisUtil, logger);
    }

    @Test
    @DisplayName("验证图形验证码时忽略大小写与首尾空白")
    void verifyCaptchaIgnoresCaseAndWhitespace() {
        when(redisUtil.get(RedisKeys.imageCaptcha(CAPTCHA_ID))).thenReturn(Mono.just("AbCd"));

        StepVerifier.create(imageCaptchaService.verifyCaptcha(CAPTCHA_ID, "  aBcD  "))
            .expectNext(true)
            .verifyComplete();
    }

    @Test
    @DisplayName("图形验证码不匹配时返回失败")
    void verifyCaptchaRejectsMismatchedText() {
        when(redisUtil.get(RedisKeys.imageCaptcha(CAPTCHA_ID))).thenReturn(Mono.just("AbCd"));

        StepVerifier.create(imageCaptchaService.verifyCaptcha(CAPTCHA_ID, "zzzz"))
            .expectNext(false)
            .verifyComplete();
    }

    @Test
    @DisplayName("图形验证码已过期时返回失败")
    void verifyCaptchaRejectsExpiredCaptcha() {
        when(redisUtil.get(RedisKeys.imageCaptcha(CAPTCHA_ID))).thenReturn(Mono.empty());

        StepVerifier.create(imageCaptchaService.verifyCaptcha(CAPTCHA_ID, "AbCd"))
            .expectNext(false)
            .verifyComplete();
    }

    @Test
    @DisplayName("提交文本为空时按失败处理且不消费验证码")
    void verifyCaptchaRejectsBlankSubmission() {
        when(redisUtil.get(RedisKeys.imageCaptcha(CAPTCHA_ID))).thenReturn(Mono.just("AbCd"));

        StepVerifier.create(imageCaptchaService.verifyCaptcha(CAPTCHA_ID, null))
            .expectNext(false)
            .verifyComplete();

        verify(redisUtil, never()).delete(anyString());
    }

    @Test
    @DisplayName("删除图形验证码时按 ID 清理 Redis")
    void deleteCaptchaRemovesStoredCaptcha() {
        when(redisUtil.delete(RedisKeys.imageCaptcha(CAPTCHA_ID))).thenReturn(Mono.just(true));

        StepVerifier.create(imageCaptchaService.deleteCaptcha(CAPTCHA_ID)).verifyComplete();

        verify(redisUtil).delete(RedisKeys.imageCaptcha(CAPTCHA_ID));
    }

    @Test
    @DisplayName("生成图形验证码时写入五分钟文本并返回图片与 ID")
    void createCaptchaStoresTextAndReturnsImage() {
        ArgumentCaptor<String> keyCaptor = ArgumentCaptor.forClass(String.class);
        ArgumentCaptor<String> textCaptor = ArgumentCaptor.forClass(String.class);
        when(redisUtil.set(keyCaptor.capture(), textCaptor.capture(), eq(CAPTCHA_TTL_SECONDS)))
            .thenReturn(Mono.just(true));

        StepVerifier.create(imageCaptchaService.createCaptcha())
            .assertNext(vo -> {
                assertThat(vo.getCaptchaId()).isNotBlank();
                assertThat(vo.getImageBase64()).isNotBlank();
                assertThat(keyCaptor.getValue()).isEqualTo(RedisKeys.imageCaptcha(vo.getCaptchaId()));
                assertThat(textCaptor.getValue()).hasSize(4);
            })
            .verifyComplete();
    }
}

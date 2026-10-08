package com.hcsy.spring.api.service.impl;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
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
import com.hcsy.spring.common.utils.Result;
import com.hcsy.spring.common.utils.SimpleLogger;
import com.hcsy.spring.entity.dto.InternalEmailCodeSendDTO;
import com.hcsy.spring.infra.client.NestjsClient;

import reactor.core.publisher.Mono;
import reactor.test.StepVerifier;

@ExtendWith(MockitoExtension.class)
class EmailVerificationServiceImplTest {

    private static final String EMAIL = "alice@example.com";
    private static final String CODE = "654321";
    private static final long CODE_TTL_SECONDS = 10 * 60;
    private static final long VERIFIED_TTL_SECONDS = 24 * 60 * 60;

    @Mock
    private RedisUtil redisUtil;
    @Mock
    private SimpleLogger logger;
    @Mock
    private NestjsClient nestjsClient;

    private EmailVerificationServiceImpl emailVerificationService;

    @BeforeEach
    void setUp() {
        emailVerificationService = new EmailVerificationServiceImpl(redisUtil, logger, nestjsClient);
    }

    @Test
    @DisplayName("发送验证码写入六位数字并将同一验证码下发给邮件服务")
    void sendVerificationCodeStoresCodeAndForwardsIt() {
        ArgumentCaptor<String> codeCaptor = ArgumentCaptor.forClass(String.class);
        when(redisUtil.set(eq(RedisKeys.emailVerify(EMAIL)), codeCaptor.capture(), eq(CODE_TTL_SECONDS)))
            .thenReturn(Mono.just(true));
        when(nestjsClient.sendEmailCode(any(InternalEmailCodeSendDTO.class))).thenReturn(okResult());

        StepVerifier.create(emailVerificationService.sendVerificationCode(EMAIL, "register")).verifyComplete();

        String storedCode = codeCaptor.getValue();
        assertThat(storedCode).matches("\\d{6}");

        ArgumentCaptor<InternalEmailCodeSendDTO> dtoCaptor = ArgumentCaptor.forClass(InternalEmailCodeSendDTO.class);
        verify(nestjsClient).sendEmailCode(dtoCaptor.capture());
        InternalEmailCodeSendDTO dto = dtoCaptor.getValue();
        assertThat(dto.getEmail()).isEqualTo(EMAIL);
        assertThat(dto.getType()).isEqualTo("register");
        assertThat(dto.getCode()).isEqualTo(storedCode);
        assertThat(dto.getExpireMinutes()).isEqualTo(10);
    }

    @Test
    @DisplayName("验证码匹配时消费验证码并返回成功")
    void verifyCodeConsumesMatchedCode() {
        when(redisUtil.get(RedisKeys.emailVerify(EMAIL))).thenReturn(Mono.just(CODE));
        when(redisUtil.delete(RedisKeys.emailVerify(EMAIL))).thenReturn(Mono.just(true));

        StepVerifier.create(emailVerificationService.verifyCode(EMAIL, CODE))
            .expectNext(true)
            .verifyComplete();

        verify(redisUtil).delete(RedisKeys.emailVerify(EMAIL));
    }

    @Test
    @DisplayName("验证码不匹配时返回失败且不消费验证码")
    void verifyCodeRejectsMismatchedCode() {
        when(redisUtil.get(RedisKeys.emailVerify(EMAIL))).thenReturn(Mono.just(CODE));

        StepVerifier.create(emailVerificationService.verifyCode(EMAIL, "000000"))
            .expectNext(false)
            .verifyComplete();

        verify(redisUtil, never()).delete(any(String.class));
    }

    @Test
    @DisplayName("验证码已过期时返回失败")
    void verifyCodeRejectsExpiredCode() {
        when(redisUtil.get(RedisKeys.emailVerify(EMAIL))).thenReturn(Mono.empty());

        StepVerifier.create(emailVerificationService.verifyCode(EMAIL, CODE))
            .expectNext(false)
            .verifyComplete();
    }

    @Test
    @DisplayName("读取验证码异常时降级为失败而不是抛错")
    void verifyCodeDegradesOnRedisFailure() {
        when(redisUtil.get(RedisKeys.emailVerify(EMAIL)))
            .thenReturn(Mono.error(new IllegalStateException("redis down")));

        StepVerifier.create(emailVerificationService.verifyCode(EMAIL, CODE))
            .expectNext(false)
            .verifyComplete();
    }

    @Test
    @DisplayName("邮箱已验证标记直接查询 Redis 是否存在")
    void isEmailVerifiedReadsRedisExistence() {
        when(redisUtil.exists(RedisKeys.emailVerified(EMAIL))).thenReturn(Mono.just(true));

        StepVerifier.create(emailVerificationService.isEmailVerified(EMAIL))
            .expectNext(true)
            .verifyComplete();
    }

    @Test
    @DisplayName("标记邮箱已验证时写入一天的标记")
    void markEmailAsVerifiedWritesOneDayFlag() {
        when(redisUtil.set(RedisKeys.emailVerified(EMAIL), "true", VERIFIED_TTL_SECONDS))
            .thenReturn(Mono.just(true));

        StepVerifier.create(emailVerificationService.markEmailAsVerified(EMAIL)).verifyComplete();

        verify(redisUtil).set(RedisKeys.emailVerified(EMAIL), "true", VERIFIED_TTL_SECONDS);
    }

    private Mono<Result<?>> okResult() {
        return Mono.just(Result.success());
    }
}

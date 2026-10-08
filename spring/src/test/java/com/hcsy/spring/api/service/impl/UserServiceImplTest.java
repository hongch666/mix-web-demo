package com.hcsy.spring.api.service.impl;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyIterable;
import static org.mockito.ArgumentMatchers.anyLong;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import java.time.LocalDateTime;
import java.util.Arrays;
import java.util.List;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.transaction.reactive.TransactionalOperator;

import com.hcsy.spring.api.repository.UserRepository;
import com.hcsy.spring.api.service.EmailVerificationService;
import com.hcsy.spring.api.service.ImageCaptchaService;
import com.hcsy.spring.api.service.TokenService;
import com.hcsy.spring.common.constants.Defaults;
import com.hcsy.spring.common.constants.HttpCode;
import com.hcsy.spring.common.constants.Messages;
import com.hcsy.spring.common.constants.RedisKeys;
import com.hcsy.spring.common.exceptions.BusinessException;
import com.hcsy.spring.common.utils.CacheUtil;
import com.hcsy.spring.common.utils.PasswordEncryptor;
import com.hcsy.spring.common.utils.RedisUtil;
import com.hcsy.spring.core.metrics.MetricsRecorder;
import com.hcsy.spring.core.properties.UserPasswordProperties;
import com.hcsy.spring.entity.dto.EmailLoginDTO;
import com.hcsy.spring.entity.dto.LoginDTO;
import com.hcsy.spring.entity.dto.UserRegisterDTO;
import com.hcsy.spring.entity.po.User;
import com.hcsy.spring.entity.vo.UserLoginVO;

import com.fasterxml.jackson.databind.ObjectMapper;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;
import reactor.test.StepVerifier;

@ExtendWith(MockitoExtension.class)
class UserServiceImplTest {

    private static final Long USER_ID = 12L;
    private static final String USERNAME = "alice";
    private static final String EMAIL = "alice@example.com";
    private static final String CAPTCHA_ID = "captcha-1";
    private static final String CAPTCHA_TEXT = "abcd";
    private static final String RAW_PASSWORD = "Passw0rd1";
    private static final String ENCODED_PASSWORD = "$2a$10$encoded";
    private static final String VERIFICATION_CODE = "123456";

    @Mock
    private UserRepository userRepository;
    @Mock
    private RedisUtil redisUtil;
    @Mock
    private TokenService tokenService;
    @Mock
    private PasswordEncryptor passwordEncryptor;
    @Mock
    private EmailVerificationService emailVerificationService;
    @Mock
    private ImageCaptchaService imageCaptchaService;
    @Mock
    private ObjectMapper objectMapper;
    @Mock
    private TransactionalOperator transactionalOperator;
    @Mock
    private CacheUtil cacheUtil;
    @Mock
    private MetricsRecorder metricsRecorder;

    private UserServiceImpl userService;

    @BeforeEach
    void setUp() {
        userService = new UserServiceImpl(userRepository, redisUtil, tokenService, passwordEncryptor,
            new UserPasswordProperties("Default123", "Reset1234"), emailVerificationService,
            imageCaptchaService, objectMapper, transactionalOperator, cacheUtil, metricsRecorder);
    }

    @Test
    @DisplayName("登录时图形验证码错误直接拒绝且不校验密码与会话")
    void loginRejectsInvalidCaptcha() {
        when(imageCaptchaService.verifyCaptcha(CAPTCHA_ID, CAPTCHA_TEXT)).thenReturn(Mono.just(false));
        when(userRepository.findByName(USERNAME)).thenReturn(Mono.empty());

        StepVerifier.create(userService.login(loginDTO()))
            .expectErrorMatches(error -> isBusinessError(error, HttpCode.UNAUTHORIZED,
                Messages.IMAGE_CAPTCHA_INVALID))
            .verify();

        verify(passwordEncryptor, never()).matchPassword(anyString(), anyString());
        verify(tokenService, never()).createLoginSession(any(), anyString());
    }

    @Test
    @DisplayName("登录时用户不存在返回未授权且不校验密码")
    void loginRejectsUnknownUser() {
        when(imageCaptchaService.verifyCaptcha(CAPTCHA_ID, CAPTCHA_TEXT)).thenReturn(Mono.just(true));
        when(userRepository.findByName(USERNAME)).thenReturn(Mono.empty());

        StepVerifier.create(userService.login(loginDTO()))
            .expectErrorMatches(error -> isBusinessError(error, HttpCode.UNAUTHORIZED, Messages.LOGIN))
            .verify();

        verify(passwordEncryptor, never()).matchPassword(anyString(), anyString());
    }

    @Test
    @DisplayName("GitHub 创建且密码隐藏的账号禁止用密码登录")
    void loginBlocksGithubAccountWithoutPassword() {
        User user = user(USERNAME);
        user.setAuthProvider("github");
        user.setPassword(Defaults.HIDE_PASSWORD);
        when(imageCaptchaService.verifyCaptcha(CAPTCHA_ID, CAPTCHA_TEXT)).thenReturn(Mono.just(true));
        when(userRepository.findByName(USERNAME)).thenReturn(Mono.just(user));
        when(tokenService.createLoginSession(USER_ID, USERNAME)).thenReturn(Mono.empty());

        StepVerifier.create(userService.login(loginDTO()))
            .expectErrorMatches(error -> isBusinessError(error, HttpCode.UNAUTHORIZED,
                Messages.GITHUB_ACCOUNT_PASSWORD_LOGIN_BLOCKED))
            .verify();

        verify(passwordEncryptor, never()).matchPassword(anyString(), anyString());
    }

    @Test
    @DisplayName("登录成功后创建会话、清理验证码并刷新最后登录时间")
    void loginCreatesSessionAndClearsCaptcha() {
        User user = user(USERNAME);
        user.setPassword(ENCODED_PASSWORD);
        UserLoginVO login = UserLoginVO.builder().accessToken("access-token").userId(USER_ID).build();
        when(imageCaptchaService.verifyCaptcha(CAPTCHA_ID, CAPTCHA_TEXT)).thenReturn(Mono.just(true));
        when(userRepository.findByName(USERNAME)).thenReturn(Mono.just(user));
        when(passwordEncryptor.matchPassword(RAW_PASSWORD, ENCODED_PASSWORD)).thenReturn(true);
        when(tokenService.createLoginSession(USER_ID, USERNAME)).thenReturn(Mono.just(login));
        stubTransactional();
        when(userRepository.save(any(User.class))).thenReturn(Mono.just(user));
        stubUserCacheEviction();
        when(imageCaptchaService.deleteCaptcha(CAPTCHA_ID)).thenReturn(Mono.empty());

        StepVerifier.create(userService.login(loginDTO()))
            .assertNext(result -> assertThat(result.getAccessToken()).isEqualTo("access-token"))
            .verifyComplete();

        verify(imageCaptchaService).deleteCaptcha(CAPTCHA_ID);
        verify(userRepository).save(any(User.class));
        assertThat(user.getLastLoginAt()).isNotNull();
    }

    @Test
    @DisplayName("密码不匹配时登录返回未授权")
    void loginRejectsWrongPassword() {
        User user = user(USERNAME);
        user.setPassword(ENCODED_PASSWORD);
        when(imageCaptchaService.verifyCaptcha(CAPTCHA_ID, CAPTCHA_TEXT)).thenReturn(Mono.just(true));
        when(userRepository.findByName(USERNAME)).thenReturn(Mono.just(user));
        when(passwordEncryptor.matchPassword(RAW_PASSWORD, ENCODED_PASSWORD)).thenReturn(false);
        when(tokenService.createLoginSession(USER_ID, USERNAME)).thenReturn(Mono.empty());

        StepVerifier.create(userService.login(loginDTO()))
            .expectErrorMatches(error -> isBusinessError(error, HttpCode.UNAUTHORIZED, Messages.LOGIN))
            .verify();

        verify(passwordEncryptor).matchPassword(RAW_PASSWORD, ENCODED_PASSWORD);
    }

    @Test
    @DisplayName("邮箱登录时图形验证码错误优先拒绝")
    void emailLoginRejectsInvalidCaptcha() {
        when(imageCaptchaService.verifyCaptcha(CAPTCHA_ID, CAPTCHA_TEXT)).thenReturn(Mono.just(false));
        when(emailVerificationService.verifyCode(EMAIL, VERIFICATION_CODE)).thenReturn(Mono.just(true));

        StepVerifier.create(userService.emailLogin(emailLoginDTO()))
            .expectErrorMatches(error -> isBusinessError(error, HttpCode.UNAUTHORIZED,
                Messages.IMAGE_CAPTCHA_INVALID))
            .verify();

        verify(emailVerificationService, never()).markEmailAsVerified(anyString());
    }

    @Test
    @DisplayName("邮箱登录时邮箱验证码错误返回未授权")
    void emailLoginRejectsInvalidEmailCode() {
        when(imageCaptchaService.verifyCaptcha(CAPTCHA_ID, CAPTCHA_TEXT)).thenReturn(Mono.just(true));
        when(emailVerificationService.verifyCode(EMAIL, VERIFICATION_CODE)).thenReturn(Mono.just(false));

        StepVerifier.create(userService.emailLogin(emailLoginDTO()))
            .expectErrorMatches(error -> isBusinessError(error, HttpCode.UNAUTHORIZED, Messages.VERIFY_CODE))
            .verify();

        verify(tokenService, never()).createLoginSession(any(), anyString());
    }

    @Test
    @DisplayName("注册时邮箱已存在返回冲突且不落库")
    void registerRejectsExistingEmail() {
        when(userRepository.findByEmail(EMAIL)).thenReturn(Mono.just(user(USERNAME)));
        when(emailVerificationService.verifyCode(EMAIL, VERIFICATION_CODE)).thenReturn(Mono.just(true));

        StepVerifier.create(userService.registerUser(registerDTO()))
            .expectErrorMatches(error -> isBusinessError(error, HttpCode.CONFLICT, Messages.EMAIL_REGISTER))
            .verify();

        verify(userRepository, never()).save(any(User.class));
    }

    @Test
    @DisplayName("注册时验证码无效返回未授权且不落库")
    void registerRejectsInvalidCode() {
        when(userRepository.findByEmail(EMAIL)).thenReturn(Mono.empty());
        when(emailVerificationService.verifyCode(EMAIL, VERIFICATION_CODE)).thenReturn(Mono.just(false));

        StepVerifier.create(userService.registerUser(registerDTO()))
            .expectErrorMatches(error -> isBusinessError(error, HttpCode.UNAUTHORIZED, Messages.VERIFY_CODE))
            .verify();

        verify(userRepository, never()).save(any(User.class));
    }

    @Test
    @DisplayName("注册成功时加密密码并按普通用户与本地来源落库")
    void registerEncryptsPasswordAndPersistsNormalUser() {
        when(userRepository.findByEmail(EMAIL)).thenReturn(Mono.empty());
        when(emailVerificationService.verifyCode(EMAIL, VERIFICATION_CODE)).thenReturn(Mono.just(true));
        when(passwordEncryptor.encryptPassword(anyString())).thenReturn(ENCODED_PASSWORD);
        stubTransactional();
        when(userRepository.save(any(User.class))).thenAnswer(invocation -> {
            User saved = invocation.getArgument(0);
            saved.setId(USER_ID);
            return Mono.just(saved);
        });
        when(redisUtil.set(anyString(), anyString())).thenReturn(Mono.just(true));
        stubUserCacheEviction();
        when(emailVerificationService.markEmailAsVerified(EMAIL)).thenReturn(Mono.empty());

        StepVerifier.create(userService.registerUser(registerDTO()))
            .assertNext(saved -> {
                assertThat(saved.getId()).isEqualTo(USER_ID);
                assertThat(saved.getPassword()).isEqualTo(ENCODED_PASSWORD);
                assertThat(saved.getRole()).isEqualTo("user");
                assertThat(saved.getAuthProvider()).isEqualTo("local");
            })
            .verifyComplete();

        verify(passwordEncryptor).encryptPassword(RAW_PASSWORD);
        verify(emailVerificationService).markEmailAsVerified(EMAIL);
    }

    @Test
    @DisplayName("批量删除时空入参直接完成且不开启事务")
    void deleteUsersByIdsSkipsEmptyInput() {
        StepVerifier.create(userService.deleteUsersAndStatusByIds(List.of())).verifyComplete();
        StepVerifier.create(userService.deleteUsersAndStatusByIds(null)).verifyComplete();

        verify(transactionalOperator, never()).transactional(any(Mono.class));
        verify(userRepository, never()).deleteAllById(anyIterable());
    }

    @Test
    @DisplayName("批量删除时存在不存在的用户则整体拒绝")
    void deleteUsersByIdsRejectsPartiallyMissingUsers() {
        when(userRepository.findAllById(List.of(1L, 2L))).thenReturn(Flux.just(user(USERNAME)));
        when(userRepository.deleteAllById(List.of(1L, 2L))).thenReturn(Mono.empty());
        stubTransactional();

        StepVerifier.create(userService.deleteUsersAndStatusByIds(List.of(1L, 2L)))
            .expectErrorMatches(error -> isBusinessError(error, HttpCode.NOT_FOUND, Messages.UNDEFINED_USERS))
            .verify();

        verify(userRepository).findAllById(List.of(1L, 2L));
    }

    @Test
    @DisplayName("批量删除时去重并跳过空 ID")
    void deleteUsersByIdsNormalizesInput() {
        when(userRepository.findAllById(List.of(1L, 2L))).thenReturn(Flux.just(user(USERNAME), user(USERNAME)));
        stubTransactional();
        when(userRepository.deleteAllById(List.of(1L, 2L))).thenReturn(Mono.empty());
        when(redisUtil.delete(anyString())).thenReturn(Mono.just(true));
        stubUserCacheEviction();

        StepVerifier.create(userService.deleteUsersAndStatusByIds(Arrays.asList(1L, null, 2L, 1L))).verifyComplete();

        verify(userRepository).deleteAllById(List.of(1L, 2L));
    }

    @Test
    @DisplayName("管理员判定对空 ID、管理员、普通用户与不存在用户分别返回预期结果")
    void isAdminUserCoversNullAdminNormalAndMissing() {
        StepVerifier.create(userService.isAdminUser(null)).expectNext(false).verifyComplete();
        verify(userRepository, never()).findById(anyLong());

        when(userRepository.findById(1L)).thenReturn(Mono.just(userWithRole("admin")));
        when(userRepository.findById(2L)).thenReturn(Mono.just(userWithRole("user")));
        when(userRepository.findById(3L)).thenReturn(Mono.empty());

        StepVerifier.create(userService.isAdminUser(1L)).expectNext(true).verifyComplete();
        StepVerifier.create(userService.isAdminUser(2L)).expectNext(false).verifyComplete();
        StepVerifier.create(userService.isAdminUser(3L)).expectNext(false).verifyComplete();
    }

    @Test
    @DisplayName("登录状态按 Redis 值映射为 1、0 与默认 0")
    void getUserLoginStatusMapsStoredValue() {
        when(redisUtil.get(RedisKeys.userStatus(1L))).thenReturn(Mono.just("1"));
        when(redisUtil.get(RedisKeys.userStatus(2L))).thenReturn(Mono.just("0"));
        when(redisUtil.get(RedisKeys.userStatus(3L))).thenReturn(Mono.empty());

        StepVerifier.create(userService.getUserLoginStatus(1L)).expectNext(1).verifyComplete();
        StepVerifier.create(userService.getUserLoginStatus(2L)).expectNext(0).verifyComplete();
        StepVerifier.create(userService.getUserLoginStatus(3L)).expectNext(0).verifyComplete();
    }

    @Test
    @DisplayName("用户名与邮箱为空时不查询数据库")
    void findBlankUsernameAndEmailReturnsEmpty() {
        StepVerifier.create(userService.findByUsername("  ")).verifyComplete();
        StepVerifier.create(userService.findByEmail(null)).verifyComplete();

        verify(userRepository, never()).findByName(anyString());
        verify(userRepository, never()).findByEmail(anyString());
    }

    @Test
    @DisplayName("增量同步按时间戳查询并转换为同步视图对象")
    void getNeo4jSyncUsersUsesUpdateAtWhenProvided() {
        LocalDateTime after = LocalDateTime.parse("2026-01-01T00:00:00");
        when(userRepository.findByUpdateAtAfter(after)).thenReturn(Flux.just(user(USERNAME)));

        StepVerifier.create(userService.getNeo4jSyncUsers("2026-01-01T00:00:00"))
            .assertNext(list -> {
                assertThat(list).hasSize(1);
                assertThat(list.get(0).getName()).isEqualTo(USERNAME);
            })
            .verifyComplete();
    }

    private void stubTransactional() {
        when(transactionalOperator.transactional(any(Mono.class)))
            .thenAnswer(invocation -> invocation.getArgument(0));
    }

    private void stubUserCacheEviction() {
        when(cacheUtil.evict(anyString(), any(CacheUtil.CacheOptions[].class))).thenReturn(Mono.empty());
    }

    private LoginDTO loginDTO() {
        return new LoginDTO(RAW_PASSWORD, USERNAME, CAPTCHA_ID, CAPTCHA_TEXT);
    }

    private EmailLoginDTO emailLoginDTO() {
        return new EmailLoginDTO(EMAIL, VERIFICATION_CODE, CAPTCHA_ID, CAPTCHA_TEXT);
    }

    private UserRegisterDTO registerDTO() {
        UserRegisterDTO dto = new UserRegisterDTO();
        dto.setName(USERNAME);
        dto.setPassword(RAW_PASSWORD);
        dto.setEmail(EMAIL);
        dto.setAge(20);
        dto.setVerificationCode(VERIFICATION_CODE);
        return dto;
    }

    private User user(String name) {
        User user = new User();
        user.setId(USER_ID);
        user.setName(name);
        user.setEmail(EMAIL);
        user.setRole("user");
        user.setAuthProvider("local");
        return user;
    }

    private User userWithRole(String role) {
        User user = user(USERNAME);
        user.setRole(role);
        return user;
    }

    private boolean isBusinessError(Throwable error, int expectedStatus, String expectedMessage) {
        return error instanceof BusinessException businessException
            && businessException.getHttpStatus() == expectedStatus
            && expectedMessage.equals(businessException.getErrorMessage());
    }
}

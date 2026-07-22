package com.hcsy.spring.api.service.impl;

import java.time.LocalDateTime;
import java.util.Collection;
import java.util.Comparator;
import java.util.List;
import java.util.UUID;

import org.springframework.stereotype.Service;
import org.springframework.transaction.reactive.TransactionalOperator;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.hcsy.spring.api.repository.UserRepository;
import com.hcsy.spring.api.service.EmailVerificationService;
import com.hcsy.spring.api.service.ImageCaptchaService;
import com.hcsy.spring.api.service.TokenService;
import com.hcsy.spring.api.service.UserService;
import com.hcsy.spring.common.constants.Defaults;
import com.hcsy.spring.common.constants.HttpCode;
import com.hcsy.spring.common.constants.Messages;
import com.hcsy.spring.common.constants.RedisKeys;
import com.hcsy.spring.common.exceptions.BusinessException;
import com.hcsy.spring.common.utils.PasswordEncryptor;
import com.hcsy.spring.common.utils.RedisUtil;
import com.hcsy.spring.common.utils.SimpleLogger;
import com.hcsy.spring.core.annotation.Neo4jSync;
import com.hcsy.spring.core.properties.UserPasswordProperties;
import com.hcsy.spring.entity.dto.EmailLoginDTO;
import com.hcsy.spring.entity.dto.GithubTokenExchangeDTO;
import com.hcsy.spring.entity.dto.GithubTokenTicketCreateDTO;
import com.hcsy.spring.entity.dto.LoginDTO;
import com.hcsy.spring.entity.dto.ResetPasswordDTO;
import com.hcsy.spring.entity.dto.UserCreateDTO;
import com.hcsy.spring.entity.dto.UserRegisterDTO;
import com.hcsy.spring.entity.dto.UserUpdateDTO;
import com.hcsy.spring.entity.po.User;
import com.hcsy.spring.entity.vo.GithubTokenTicketVO;
import com.hcsy.spring.entity.vo.UserListVO;
import com.hcsy.spring.entity.vo.UserLoginVO;
import com.hcsy.spring.entity.vo.UserVO;

import cn.hutool.core.bean.BeanUtil;
import lombok.RequiredArgsConstructor;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;
import reactor.core.scheduler.Schedulers;

@Service
@RequiredArgsConstructor
public class UserServiceImpl implements UserService {
    private static final String AI_ROLE = "ai";
    private static final long GITHUB_TOKEN_TICKET_TTL_SECONDS = 60L;
    private static final long ALL_USERS_CACHE_TTL_SECONDS = 24 * 60 * 60L;
    private static final String GITHUB_TOKEN_TICKET_PREFIX = "oauth:github:token:";
    private static final String ALL_USERS_CACHE_KEY = "user:page:all-users";

    private final UserRepository userRepository;
    private final RedisUtil redisUtil;
    private final TokenService tokenService;
    private final PasswordEncryptor passwordEncryptor;
    private final UserPasswordProperties userPasswordProperties;
    private final EmailVerificationService emailVerificationService;
    private final ImageCaptchaService imageCaptchaService;
    private final ObjectMapper objectMapper;
    private final SimpleLogger logger;
    private final TransactionalOperator transactionalOperator;

    @Override
    public Mono<UserListVO> listUsersWithFilter(long page, long size, String username) {
        Flux<User> query = hasText(username)
                ? userRepository.findByRoleNotAndNameContainingOrderByIdAsc(AI_ROLE, username)
                : userRepository.findByRoleNotOrderByIdAsc(AI_ROLE);

        return query.collectList().flatMap(users -> {
            if (users.isEmpty()) {
                return Mono.just(userList(List.of(), 0));
            }
            List<String> statusKeys = users.stream().map(user -> RedisKeys.userStatus(user.getId())).toList();
            return redisUtil.batchGet(statusKeys)
                    .onErrorReturn(List.of())
                    .flatMap(statuses -> toPagedUserList(users, statuses, page, size));
        });
    }

    @SuppressWarnings("null")
    private Mono<UserListVO> toPagedUserList(List<User> users, List<String> statuses, long page, long size) {
        for (int index = 0; index < users.size(); index++) {
            String status = index < statuses.size() ? statuses.get(index) : null;
            users.get(index).setLoginStatus("1".equals(status) ? 1 : 0);
        }
        users.sort(Comparator.comparing(User::getLoginStatus).reversed().thenComparing(User::getId));
        int from = (int) Math.min(users.size(), Math.max(0, page - 1) * Math.max(1, size));
        int to = (int) Math.min(users.size(), from + Math.max(1, size));
        List<User> paged = users.subList(from, to);

        return Flux.fromIterable(paged)
                .flatMapSequential(user -> tokenService.getUserOnlineDeviceCount(user.getId())
                        .map(deviceCount -> {
                            UserVO vo = BeanUtil.copyProperties(user, UserVO.class);
                            vo.setLoginStatus(user.getLoginStatus());
                            vo.setOnlineDeviceCount(deviceCount);
                            return vo;
                        }), 8)
                .collectList()
                .map(records -> userList(records, users.size()));
    }

    @SuppressWarnings("null")
    @Override
    @Neo4jSync(description = Messages.NEO4J_SYNC_DESC_USER_DELETE)
    public Mono<Void> deleteUserAndStatusById(Long id) {
        Mono<Void> databaseOperation = userRepository.findById(id)
                .switchIfEmpty(Mono.error(notFound(Messages.UNDEFINED_USER)))
                .flatMap(userRepository::delete);
        return transactionalOperator.transactional(databaseOperation)
                .then(Mono.when(evictAllUsersCache(), redisUtil.delete(RedisKeys.userStatus(id))).then());
    }

    @SuppressWarnings("null")
    @Override
    @Neo4jSync(description = Messages.NEO4J_SYNC_DESC_USER_BATCH_DELETE)
    public Mono<Void> deleteUsersAndStatusByIds(List<Long> ids) {
        List<Long> distinctIds = normalizeIds(ids);
        if (distinctIds.isEmpty()) {
            return Mono.empty();
        }
        Mono<Void> databaseOperation = userRepository.findAllById(distinctIds)
                .count()
                .filter(count -> count == distinctIds.size())
                .switchIfEmpty(Mono.error(notFound(Messages.UNDEFINED_USERS)))
                .then(userRepository.deleteAllById(distinctIds));
        Mono<Void> clearStatuses = Flux.fromIterable(distinctIds)
                .flatMap(id -> redisUtil.delete(RedisKeys.userStatus(id)), 8)
                .then();
        return transactionalOperator.transactional(databaseOperation)
                .then(Mono.when(evictAllUsersCache(), clearStatuses));
    }

    @Override
    public Mono<User> findByUsername(String username) {
        return hasText(username) ? userRepository.findByName(username) : Mono.empty();
    }

    @Override
    public Mono<User> findByEmail(String email) {
        return hasText(email) ? userRepository.findByEmail(email) : Mono.empty();
    }

    @Override
    public Flux<User> listAllUserByUsername(String username) {
        return hasText(username) ? userRepository.findByNameContaining(username) : userRepository.findAll();
    }

    @Override
    public Mono<UserLoginVO> login(LoginDTO loginDTO) {
        return validateLoginCaptcha(loginDTO.getCaptchaId(), loginDTO.getCaptchaText())
                .then(findByUsername(loginDTO.getName())
                        .switchIfEmpty(Mono.error(unauthorized(Messages.LOGIN))))
                .flatMap(user -> validatePassword(loginDTO.getPassword(), user).then(loginUser(user)))
                .flatMap(login -> imageCaptchaService.deleteCaptcha(loginDTO.getCaptchaId()).thenReturn(login));
    }

    @Override
    public Mono<UserLoginVO> emailLogin(EmailLoginDTO dto) {
        Mono<Boolean> captchaValid = imageCaptchaService.verifyCaptcha(dto.getCaptchaId(), dto.getCaptchaText());
        Mono<Boolean> emailCodeValid = emailVerificationService.verifyCode(dto.getEmail(), dto.getVerificationCode());
        return Mono.zip(captchaValid, emailCodeValid)
                .flatMap(valid -> {
                    if (!valid.getT1()) {
                        return Mono.error(unauthorized(Messages.IMAGE_CAPTCHA_INVALID));
                    }
                    if (!valid.getT2()) {
                        return Mono.error(unauthorized(Messages.VERIFY_CODE));
                    }
                    return findByEmail(dto.getEmail())
                            .switchIfEmpty(Mono.error(notFound(Messages.UNDEFINED_USER_REGISTER)));
                })
                .flatMap(this::loginUser)
                .flatMap(login -> imageCaptchaService.deleteCaptcha(dto.getCaptchaId()).thenReturn(login));
    }

    private Mono<UserLoginVO> loginUser(User user) {
        return tokenService.createLoginSession(user.getId(), user.getName())
                .flatMap(login -> markLastLoginTime(user).thenReturn(login));
    }

    @Override
    public Mono<GithubTokenTicketVO> createGithubTokenTicket(GithubTokenTicketCreateDTO dto) {
        return userRepository.findById(dto.getUserId().longValue())
                .switchIfEmpty(Mono.error(notFound(Messages.UNDEFINED_USER)))
                .flatMap(user -> tokenService.createLoginSession(user.getId(), user.getName()))
                .flatMap(login -> {
                    String ticket = UUID.randomUUID().toString().replace("-", "");
                    return Mono.fromCallable(() -> objectMapper.writeValueAsString(login))
                            .flatMap(json -> redisUtil.set(buildGithubTicketKey(ticket), json,
                                    GITHUB_TOKEN_TICKET_TTL_SECONDS))
                            .onErrorResume(error -> tokenService.removeSessionByAccessToken(login.getAccessToken())
                                    .then(Mono.error(BusinessException.builder()
                                            .httpStatus(HttpCode.INTERNAL_SERVER_ERROR)
                                            .errorMessage(Messages.GITHUB_LOGIN_TICKET_CACHE_FAILED)
                                            .cause(error).build())))
                            .then(evictAllUsersCache())
                            .thenReturn(GithubTokenTicketVO.builder()
                                    .ticket(ticket)
                                    .expiresIn(GITHUB_TOKEN_TICKET_TTL_SECONDS)
                                    .build());
                });
    }

    @Override
    public Mono<UserLoginVO> exchangeGithubTokenTicket(GithubTokenExchangeDTO dto) {
        String ticket = dto.getTicket() == null ? "" : dto.getTicket().trim();
        if (ticket.isEmpty()) {
            return Mono.error(BusinessException.builder().httpStatus(HttpCode.BAD_REQUEST)
                    .errorMessage(Messages.GITHUB_TOKEN_TICKET_EMPTY).build());
        }
        String key = buildGithubTicketKey(ticket);
        return redisUtil.get(key)
                .switchIfEmpty(Mono.error(unauthorized(Messages.GITHUB_TOKEN_TICKET_EXPIRED)))
                .flatMap(json -> redisUtil.delete(key)
                        .then(Mono.fromCallable(() -> objectMapper.readValue(json, UserLoginVO.class))))
                .onErrorMap(error -> error instanceof BusinessException ? error
                        : BusinessException.builder()
                                .httpStatus(HttpCode.INTERNAL_SERVER_ERROR)
                                .errorMessage(Messages.GITHUB_TOKEN_TICKET_PARSE_FAILED)
                                .cause(error).build());
    }

    @Override
    public Mono<Void> registerUser(UserRegisterDTO dto) {
        Mono<Boolean> emailAvailable = findByEmail(dto.getEmail()).hasElement().map(exists -> !exists);
        Mono<Boolean> codeValid = emailVerificationService.verifyCode(dto.getEmail(), dto.getVerificationCode());
        return Mono.zip(emailAvailable, codeValid)
                .flatMap(valid -> {
                    if (!valid.getT1()) {
                        return Mono.error(conflict(Messages.EMAIL_REGISTER));
                    }
                    if (!valid.getT2()) {
                        return Mono.error(unauthorized(Messages.VERIFY_CODE));
                    }
                    User user = BeanUtil.copyProperties(dto, User.class);
                    user.setRole("user");
                    user.setAuthProvider("local");
                    return encryptPassword(user.getPassword()).flatMap(password -> {
                        user.setPassword(password);
                        return saveUserAndStatus(user);
                    });
                })
                .then(emailVerificationService.markEmailAsVerified(dto.getEmail()))
                .then(evictAllUsersCache());
    }

    @Override
    public Mono<UserListVO> getAllUsers(String username) {
        boolean useCache = !hasText(username);
        Mono<UserListVO> cached = useCache
                ? redisUtil.get(ALL_USERS_CACHE_KEY)
                        .flatMap(json -> Mono.fromCallable(() -> objectMapper.readValue(json, UserListVO.class)))
                        .onErrorResume(error -> {
                            logger.error(Messages.USER_LIST_CACHE_READ_FAILED, error.getMessage(), error);
                            return Mono.empty();
                        })
                : Mono.empty();
        return cached.switchIfEmpty(Mono.defer(() -> loadAllUsers(username)
                .flatMap(result -> useCache ? writeUsersCache(result).thenReturn(result) : Mono.just(result))));
    }

    private Mono<UserListVO> loadAllUsers(String username) {
        Flux<User> users = hasText(username)
                ? userRepository.findByRoleNotAndNameContainingOrderByIdAsc(AI_ROLE, username)
                : userRepository.findByRoleNotOrderByIdAsc(AI_ROLE);
        return users.map(user -> BeanUtil.copyProperties(user, UserVO.class))
                .collectList()
                .map(records -> userList(records, records.size()));
    }

    @Override
    public Mono<UserListVO> getAllAiUsers() {
        return userRepository.findByRoleOrderByIdAsc(AI_ROLE)
                .map(user -> BeanUtil.copyProperties(user, UserVO.class))
                .collectList()
                .map(records -> userList(records, records.size()));
    }

    @Override
    public Flux<Long> getNormalUserIds() {
        return userRepository.findIdsByRoleNot(AI_ROLE);
    }

    @Override
    public Flux<Long> getAiUserIds() {
        return userRepository.findIdsByRole(AI_ROLE);
    }

    @Override
    public Mono<Long> countNormalUsers() {
        return userRepository.countByRoleNot(AI_ROLE);
    }

    @Override
    public Mono<Long> countAiUsers() {
        return userRepository.countByRole(AI_ROLE);
    }

    @Override
    @Neo4jSync(description = Messages.NEO4J_SYNC_DESC_USER_SAVE)
    public Mono<User> saveUserAndStatus(User user) {
        if (!hasText(user.getAuthProvider())) {
            user.setAuthProvider("local");
        }
        Mono<String> password = isEncoded(user.getPassword())
                ? Mono.justOrEmpty(user.getPassword())
                : encryptPassword(user.getPassword());
        return password.defaultIfEmpty("")
                .flatMap(encoded -> {
                    if (!encoded.isEmpty()) {
                        user.setPassword(encoded);
                    }
                    return transactionalOperator.transactional(userRepository.save(user));
                })
                .flatMap(saved -> redisUtil.set(RedisKeys.userStatus(saved.getId()), "0").thenReturn(saved));
    }

    @Override
    public Mono<Integer> getUserLoginStatus(Long userId) {
        return redisUtil.get(RedisKeys.userStatus(userId)).map(status -> "1".equals(status) ? 1 : 0).defaultIfEmpty(0);
    }

    @Override
    public Mono<Void> updateUserStatus(Long userId, String status) {
        return redisUtil.set(RedisKeys.userStatus(userId), status).then(evictAllUsersCache());
    }

    @Override
    @Neo4jSync(description = Messages.NEO4J_SYNC_DESC_USER_SAVE)
    public Mono<Void> createUser(UserCreateDTO dto) {
        User user = BeanUtil.copyProperties(dto, User.class);
        user.setRole("user");
        user.setAuthProvider("local");
        String rawPassword = hasText(user.getPassword()) ? user.getPassword()
                : userPasswordProperties.getDefaultPassword();
        return encryptPassword(rawPassword)
                .flatMap(password -> {
                    user.setPassword(password);
                    return saveUserAndStatus(user);
                })
                .then(evictAllUsersCache());
    }

    @Override
    @Neo4jSync(description = Messages.NEO4J_SYNC_DESC_USER_UPDATE)
    public Mono<Void> updateUserInfo(UserUpdateDTO dto) {
        return userRepository.findById(dto.getId().longValue())
                .switchIfEmpty(Mono.error(notFound(Messages.UNDEFINED_USER)))
                .flatMap(existing -> {
                    User user = BeanUtil.copyProperties(dto, User.class);
                    user.setGithubId(existing.getGithubId());
                    user.setGithubLogin(existing.getGithubLogin());
                    user.setGithubUrl(existing.getGithubUrl());
                    user.setAuthProvider(existing.getAuthProvider());
                    user.setLastLoginAt(existing.getLastLoginAt());
                    user.setCreateAt(existing.getCreateAt());
                    Mono<String> password = hasText(dto.getPassword())
                            ? encryptPassword(dto.getPassword())
                            : Mono.just(existing.getPassword());
                    return password.flatMap(encoded -> {
                        user.setPassword(encoded);
                        return transactionalOperator.transactional(userRepository.save(user));
                    });
                })
                .then(evictAllUsersCache());
    }

    @Override
    public Mono<Void> resetPassword(ResetPasswordDTO dto) {
        return emailVerificationService.verifyCode(dto.getEmail(), dto.getVerificationCode())
                .filter(Boolean.TRUE::equals)
                .switchIfEmpty(Mono.error(unauthorized(Messages.VERIFY_CODE)))
                .then(findByEmail(dto.getEmail()).switchIfEmpty(Mono.error(notFound(Messages.UNDEFINED_USER))))
                .flatMap(user -> encryptPassword(dto.getNewPassword()).flatMap(password -> {
                    user.setPassword(password);
                    return transactionalOperator.transactional(userRepository.save(user));
                }))
                .then();
    }

    @Override
    public Mono<Void> resetAllPasswords() {
        return userRepository.count()
                .filter(count -> count > 0)
                .switchIfEmpty(Mono.error(BusinessException.builder().httpStatus(HttpCode.UNPROCESSABLE_ENTITY)
                        .errorMessage(Messages.PASSWORD_NO_USER).build()))
                .then(encryptPassword(userPasswordProperties.getResetPassword()))
                .flatMap(userRepository::updateAllPasswords)
                .then();
    }

    @SuppressWarnings("null")
    @Override
    public Mono<Void> resetUserPassword(Long userId) {
        return userRepository.findById(userId)
                .switchIfEmpty(Mono.error(notFound(Messages.UNDEFINED_USER)))
                .flatMap(user -> encryptPassword(userPasswordProperties.getResetPassword()).flatMap(password -> {
                    user.setPassword(password);
                    return transactionalOperator.transactional(userRepository.save(user));
                }))
                .then();
    }

    @SuppressWarnings("null")
    @Override
    public Mono<User> getById(Long id) {
        return userRepository.findById(id);
    }

    @SuppressWarnings("null")
    @Override
    public Flux<User> listByIds(Collection<Long> ids) {
        return userRepository.findAllById(ids);
    }

    private Mono<Void> markLastLoginTime(User user) {
        user.setLastLoginAt(LocalDateTime.now());
        return transactionalOperator.transactional(userRepository.save(user)).then();
    }

    private Mono<Void> validateLoginCaptcha(String captchaId, String captchaText) {
        return imageCaptchaService.verifyCaptcha(captchaId, captchaText)
                .filter(Boolean.TRUE::equals)
                .switchIfEmpty(Mono.error(unauthorized(Messages.IMAGE_CAPTCHA_INVALID)))
                .then();
    }

    private Mono<Void> validatePassword(String rawPassword, User user) {
        if ("github".equalsIgnoreCase(user.getAuthProvider()) && Defaults.HIDE_PASSWORD.equals(user.getPassword())) {
            return Mono.error(unauthorized(Messages.GITHUB_ACCOUNT_PASSWORD_LOGIN_BLOCKED));
        }
        return Mono.fromCallable(() -> passwordEncryptor.matchPassword(rawPassword, user.getPassword()))
                .subscribeOn(Schedulers.boundedElastic())
                .filter(Boolean.TRUE::equals)
                .switchIfEmpty(Mono.error(unauthorized(Messages.LOGIN)))
                .then();
    }

    private Mono<String> encryptPassword(String rawPassword) {
        return Mono.fromCallable(() -> passwordEncryptor.encryptPassword(rawPassword))
                .subscribeOn(Schedulers.boundedElastic());
    }

    private Mono<Void> writeUsersCache(UserListVO result) {
        long ttl = result.getTotal() == 0 ? 10 * 60L : ALL_USERS_CACHE_TTL_SECONDS;
        return Mono.fromCallable(() -> objectMapper.writeValueAsString(result))
                .flatMap(json -> redisUtil.set(ALL_USERS_CACHE_KEY, json, ttl))
                .onErrorResume(error -> {
                    logger.error(Messages.USER_LIST_CACHE_WRITE_FAILED, error.getMessage(), error);
                    return Mono.just(false);
                })
                .then();
    }

    private Mono<Void> evictAllUsersCache() {
        return redisUtil.delete(ALL_USERS_CACHE_KEY)
                .onErrorResume(error -> {
                    logger.error(Messages.USER_LIST_CACHE_EVICT_FAILED, error.getMessage(), error);
                    return Mono.just(false);
                })
                .then();
    }

    private UserListVO userList(List<UserVO> users, long total) {
        return UserListVO.builder().total(total).list(users).build();
    }

    private boolean hasText(String value) {
        return value != null && !value.isBlank();
    }

    private boolean isEncoded(String password) {
        return password != null && (password.startsWith("$2a$") || password.startsWith("$2b$")
                || password.startsWith("$2x$") || password.startsWith("$2y$"));
    }

    private List<Long> normalizeIds(List<Long> ids) {
        return ids == null ? List.of() : ids.stream().filter(id -> id != null).distinct().toList();
    }

    private String buildGithubTicketKey(String ticket) {
        return GITHUB_TOKEN_TICKET_PREFIX + ticket;
    }

    private BusinessException notFound(String message) {
        return BusinessException.builder().httpStatus(HttpCode.NOT_FOUND).errorMessage(message).build();
    }

    private BusinessException unauthorized(String message) {
        return BusinessException.builder().httpStatus(HttpCode.UNAUTHORIZED).errorMessage(message).build();
    }

    private BusinessException conflict(String message) {
        return BusinessException.builder().httpStatus(HttpCode.CONFLICT).errorMessage(message).build();
    }
}

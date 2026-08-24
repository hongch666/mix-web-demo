package com.hcsy.spring.api.service.impl;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.Collection;
import java.util.Comparator;
import java.util.List;
import java.util.Map;
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
import com.hcsy.spring.common.utils.CacheUtil;
import com.hcsy.spring.common.utils.Neo4jSyncMapUtil;
import com.hcsy.spring.common.utils.PasswordEncryptor;
import com.hcsy.spring.common.utils.RedisUtil;
import com.hcsy.spring.core.annotation.Neo4jSync;
import com.hcsy.spring.core.properties.UserPasswordProperties;
import com.hcsy.spring.entity.dto.EmailLoginDTO;
import com.hcsy.spring.entity.dto.GithubTokenExchangeDTO;
import com.hcsy.spring.entity.dto.GithubTokenTicketCreateDTO;
import com.hcsy.spring.entity.dto.GithubUserInternalDTO;
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
    private static final CacheUtil.CacheOptions<UserListVO> ALL_USERS_CACHE = CacheUtil.CacheOptions.fixed(
        RedisKeys.allUsersCacheName(), RedisKeys.userCacheInvalidationChannel(), 1);

    private final UserRepository userRepository;
    private final RedisUtil redisUtil;
    private final TokenService tokenService;
    private final PasswordEncryptor passwordEncryptor;
    private final UserPasswordProperties userPasswordProperties;
    private final EmailVerificationService emailVerificationService;
    private final ImageCaptchaService imageCaptchaService;
    private final ObjectMapper objectMapper;
    private final TransactionalOperator transactionalOperator;
    private final CacheUtil cacheUtil;

    @Override
    public Mono<UserListVO> listUsersWithFilter(long page, long size, String username) {
        Flux<User> query = hasText(username)
            ? userRepository.findByRoleNotAndNameContainingOrderByIdAsc(Defaults.AI_ROLE, username)
            : userRepository.findByRoleNotOrderByIdAsc(Defaults.AI_ROLE);

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

    @Override
    @Neo4jSync(description = "删除用户后同步 Neo4j")
    public Mono<Void> deleteUserAndStatusById(Long id) {
        Mono<Void> databaseOperation = userRepository.findById(id)
            .switchIfEmpty(Mono.error(notFound(Messages.UNDEFINED_USER)))
            .flatMap(userRepository::delete);
        return transactionalOperator.transactional(databaseOperation)
            .then(Mono.when(evictAllUsersCache(), redisUtil.delete(RedisKeys.userStatus(id))).then());
    }

    @Override
    @Neo4jSync(description = "批量删除用户后同步 Neo4j")
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
            .flatMap(login -> {
                imageCaptchaService.deleteCaptcha(loginDTO.getCaptchaId()).subscribe();
                return Mono.just(login);
            });
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
                    .flatMap(json -> redisUtil.set(RedisKeys.githubTokenTicket(ticket), json,
                        Defaults.GITHUB_TOKEN_TICKET_TTL_SECONDS))
                    .onErrorResume(error -> tokenService.removeSessionByAccessToken(login.getAccessToken())
                        .then(Mono.error(BusinessException.builder()
                            .httpStatus(HttpCode.INTERNAL_SERVER_ERROR)
                            .errorMessage(Messages.GITHUB_LOGIN_TICKET_CACHE_FAILED)
                            .cause(error).build())))
                    .then(evictAllUsersCache())
                    .thenReturn(GithubTokenTicketVO.builder()
                        .ticket(ticket)
                        .expiresIn(Defaults.GITHUB_TOKEN_TICKET_TTL_SECONDS)
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
        String key = RedisKeys.githubTokenTicket(ticket);
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
            .then();
    }

    @Override
    public Mono<UserListVO> getAllUsers(String username) {
        if (!hasText(username)) {
            return getAllUsersFromCache();
        }
        return loadUsersByUsername(username);
    }

    private Mono<UserListVO> getAllUsersFromCache() {
        return cacheUtil.get(ALL_USERS_CACHE, RedisKeys.allUsersCache(), RedisKeys.allUsersCache(),
            UserListVO.class, this::loadAllUsers);
    }

    private Mono<UserListVO> loadAllUsers() {
        return userRepository.findByRoleNotOrderByIdAsc(Defaults.AI_ROLE)
            .map(user -> BeanUtil.copyProperties(user, UserVO.class))
            .collectList()
            .map(records -> userList(records, records.size()));
    }

    private Mono<UserListVO> loadUsersByUsername(String username) {
        return userRepository.findByRoleNotAndNameContainingOrderByIdAsc(Defaults.AI_ROLE, username)
            .map(user -> BeanUtil.copyProperties(user, UserVO.class))
            .collectList()
            .map(records -> userList(records, records.size()));
    }

    @Override
    public Mono<UserListVO> getAllAiUsers() {
        return userRepository.findByRoleOrderByIdAsc(Defaults.AI_ROLE)
            .map(user -> BeanUtil.copyProperties(user, UserVO.class))
            .collectList()
            .map(records -> userList(records, records.size()));
    }

    @Override
    public Flux<Long> getNormalUserIds() {
        return userRepository.findIdsByRoleNot(Defaults.AI_ROLE);
    }

    @Override
    public Flux<Long> getAiUserIds() {
        return userRepository.findIdsByRole(Defaults.AI_ROLE);
    }

    @Override
    public Mono<Long> countNormalUsers() {
        return userRepository.countByRoleNot(Defaults.AI_ROLE);
    }

    @Override
    public Mono<Long> countAiUsers() {
        return userRepository.countByRole(Defaults.AI_ROLE);
    }

    @Override
    @Neo4jSync(description = "保存用户后同步 Neo4j")
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
            .flatMap(saved -> Mono.when(
                redisUtil.set(RedisKeys.userStatus(saved.getId()), "0"),
                evictAllUsersCache()).thenReturn(saved));
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
    @Neo4jSync(description = "保存用户后同步 Neo4j")
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
            .then();
    }

    @Override
    @Neo4jSync(description = "修改用户后同步 Neo4j")
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
                user.setUpdateAt(LocalDateTime.now());
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

    @Override
    public Mono<User> findByGithubId(Long githubId) {
        if (githubId == null) {
            return Mono.empty();
        }
        return userRepository.findByGithubId(githubId);
    }

    @Override
    public Mono<User> findOrCreateGithubUser(GithubUserInternalDTO dto) {
        String githubId = dto.getGithubId();
        return userRepository.findByGithubId(Long.valueOf(githubId))
            .flatMap(existingUser -> {
                existingUser.setGithubLogin(dto.getGithubLogin());
                existingUser.setGithubUrl(dto.getGithubUrl());
                existingUser.setImg(dto.getAvatarUrl());
                if (dto.getEmail() != null && !dto.getEmail().isBlank()) {
                    existingUser.setEmail(dto.getEmail());
                }
                existingUser.setAuthProvider("github");
                existingUser.setLastLoginAt(LocalDateTime.now());
                return transactionalOperator.transactional(userRepository.save(existingUser));
            })
            .switchIfEmpty(Mono.defer(() -> {
                User newUser = new User();
                newUser.setGithubId(Long.valueOf(githubId));
                newUser.setGithubLogin(dto.getGithubLogin());
                newUser.setGithubUrl(dto.getGithubUrl());
                newUser.setName(dto.getGithubName() != null && !dto.getGithubName().isBlank()
                    ? dto.getGithubName()
                    : dto.getGithubLogin());
                newUser.setEmail(dto.getEmail());
                newUser.setImg(dto.getAvatarUrl());
                newUser.setAge(18);
                newUser.setRole("user");
                newUser.setAuthProvider("github");
                newUser.setLastLoginAt(LocalDateTime.now());
                return encryptPassword(userPasswordProperties.getDefaultPassword())
                    .flatMap(password -> {
                        newUser.setPassword(password);
                        return saveUserAndStatus(newUser);
                    })
                    .flatMap(saved -> evictAllUsersCache().thenReturn(saved));
            }));
    }

    @Override
    public Mono<Boolean> isAdminUser(Long userId) {
        if (userId == null) {
            return Mono.just(false);
        }
        return userRepository.findById(userId)
            .map(user -> "admin".equalsIgnoreCase(user.getRole()))
            .defaultIfEmpty(false);
    }

    @Override
    public Mono<User> getById(Long id) {
        return userRepository.findById(id);
    }

    @Override
    public Flux<User> listByIds(Collection<Long> ids) {
        return userRepository.findAllById(ids);
    }

    @Override
    public Mono<List<Map<String, Object>>> getNeo4jSyncUsers(String updatedAfter) {
        if (updatedAfter == null || updatedAfter.isBlank()) {
            return userRepository.findAll()
                .map(Neo4jSyncMapUtil::userToMap)
                .collectList()
                .map(list -> list.isEmpty() ? new ArrayList<>() : list);
        }
        LocalDateTime after = LocalDateTime.parse(updatedAfter);
        return userRepository.findByUpdateAtAfter(after)
            .map(Neo4jSyncMapUtil::userToMap)
            .collectList()
            .map(list -> list.isEmpty() ? new ArrayList<>() : list);
    }

    private Mono<Void> markLastLoginTime(User user) {
        user.setLastLoginAt(LocalDateTime.now());
        return transactionalOperator.transactional(userRepository.save(user))
            .then(evictAllUsersCache());
    }

    private Mono<Void> evictAllUsersCache() {
        return cacheUtil.evict(RedisKeys.allUsersCache(), ALL_USERS_CACHE);
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

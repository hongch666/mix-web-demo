package com.hcsy.spring.application.service.impl;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.Collection;
import java.util.Comparator;
import java.util.List;
import java.util.UUID;

import org.springframework.stereotype.Service;
import org.springframework.transaction.reactive.TransactionalOperator;

import com.hcsy.spring.application.service.EmailVerificationService;
import com.hcsy.spring.application.service.ImageCaptchaService;
import com.hcsy.spring.application.service.TokenService;
import com.hcsy.spring.application.service.UserService;
import com.hcsy.spring.common.constants.Defaults;
import com.hcsy.spring.common.constants.HttpCode;
import com.hcsy.spring.common.constants.Messages;
import com.hcsy.spring.common.constants.MetricNames;
import com.hcsy.spring.common.constants.RedisKeys;
import com.hcsy.spring.common.exceptions.BusinessException;
import com.hcsy.spring.common.utils.CacheUtil;
import com.hcsy.spring.common.utils.PasswordEncryptor;
import com.hcsy.spring.common.utils.RedisUtil;
import com.hcsy.spring.config.properties.UserPasswordProperties;
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
import com.hcsy.spring.entity.vo.KickOtherDevicesVO;
import com.hcsy.spring.entity.vo.UserListVO;
import com.hcsy.spring.entity.vo.UserLoginVO;
import com.hcsy.spring.entity.vo.UserSyncVO;
import com.hcsy.spring.entity.vo.UserVO;
import com.hcsy.spring.infra.repository.UserRepository;
import com.hcsy.spring.observability.MetricsRecorder;

import cn.hutool.core.bean.BeanUtil;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;
import reactor.core.scheduler.Schedulers;

/**
 * UserService 的实现，聚合密码加密、验证码校验、令牌会话与多级缓存，实现用户注册登录、资料维护、多设备踢出与用户统计等能力
 */
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
    private final MetricsRecorder metricsRecorder;

    /**
     * 根据ID查询用户并组装登录状态与在线设备数返回用户详情
     */
    @Override
    public Mono<UserVO> getUserDetail(Long id) {
        return getById(id).flatMap(user -> Mono.zip(
            getUserLoginStatus(id), tokenService.getUserOnlineDeviceCount(id))
            .map(status -> {
                UserVO vo = BeanUtil.copyProperties(user, UserVO.class);
                vo.setLoginStatus(status.getT1());
                vo.setOnlineDeviceCount(status.getT2());
                return vo;
            }));
    }

    /**
     * 调用令牌服务移除当前会话外的其他设备会话，返回移除数与剩余在线设备数
     */
    @Override
    public Mono<KickOtherDevicesVO> kickOtherDevices(Long userId, String accessToken) {
        return tokenService.removeOtherSessions(userId, accessToken)
            .flatMap(removed -> tokenService.getUserOnlineDeviceCount(userId)
                .map(remaining -> KickOtherDevicesVO.builder()
                    .userId(userId)
                    .removedSessionCount(removed)
                    .onlineDeviceCount(remaining)
                    .build()));
    }

    /**
     * 用户存在时强制其下线并返回true，用户不存在时返回false
     */
    @Override
    public Mono<Boolean> forceLogoutUser(Long userId) {
        return getById(userId)
            .flatMap(user -> tokenService.forceLogoutUser(userId).thenReturn(true))
            .defaultIfEmpty(false);
    }

    /**
     * 校验邮箱格式与用途类型，并按注册登录重置场景检查邮箱存在性后发送验证码，返回发送结果
     */
    @Override
    public Mono<EmailCodeSendOutcome> sendVerificationCode(String email, String type) {
        if (email == null || !email.matches("^[A-Za-z0-9+_.-]+@(.+)$")) {
            return Mono.just(EmailCodeSendOutcome.INVALID_EMAIL);
        }
        if (!"register".equals(type) && !"login".equals(type) && !"reset".equals(type)) {
            return Mono.just(EmailCodeSendOutcome.INVALID_TYPE);
        }
        return findByEmail(email).hasElement().flatMap(exists -> {
            if ("register".equals(type) && exists) {
                return Mono.just(EmailCodeSendOutcome.EMAIL_EXISTS);
            }
            if (!"register".equals(type) && !exists) {
                return Mono.just(EmailCodeSendOutcome.EMAIL_NOT_FOUND);
            }
            return emailVerificationService.sendVerificationCode(email, type)
                .thenReturn(EmailCodeSendOutcome.SENT);
        });
    }

    /**
     * 查询非AI用户并批量读取登录状态，按在线优先与ID排序后内存分页组装用户列表
     */
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

    /**
     * 为用户填充登录状态并按在线优先排序，内存分页后逐个补齐在线设备数组装分页列表VO
     */
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

    /**
     * 事务删除指定用户后清理其登录状态、角色缓存与全量用户缓存
     */
    @Override
    public Mono<Void> deleteUserAndStatusById(Long id) {
        Mono<Void> databaseOperation = userRepository.findById(id)
            .switchIfEmpty(Mono.error(notFound(Messages.UNDEFINED_USER)))
            .flatMap(userRepository::delete);
        return transactionalOperator.transactional(databaseOperation)
            .then(Mono.when(evictAllUsersCache(), redisUtil.delete(RedisKeys.userStatus(id)),
                evictUserRoleCache(id)));
    }

    /**
     * 校验全部用户存在后事务批量删除，并并发清理各用户的登录状态与角色缓存
     */
    @Override
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
        Mono<Void> clearRoles = Flux.fromIterable(distinctIds)
            .flatMap(this::evictUserRoleCache, 8)
            .then();
        return transactionalOperator.transactional(databaseOperation)
            .then(Mono.when(evictAllUsersCache(), clearStatuses, clearRoles));
    }

    /**
     * 用户名非空时按名称精确查询用户，否则返回空的Mono
     */
    @Override
    public Mono<User> findByUsername(String username) {
        return hasText(username) ? userRepository.findByName(username) : Mono.empty();
    }

    /**
     * 邮箱非空时按邮箱精确查询用户，否则返回空的Mono
     */
    @Override
    public Mono<User> findByEmail(String email) {
        return hasText(email) ? userRepository.findByEmail(email) : Mono.empty();
    }

    /**
     * 用户名非空时模糊匹配查询用户，否则返回全部用户的Flux流
     */
    @Override
    public Flux<User> listAllUserByUsername(String username) {
        return hasText(username) ? userRepository.findByNameContaining(username) : userRepository.findAll();
    }

    /**
     * 校验图形验证码、用户存在性与密码匹配后创建登录会话并清除验证码，记录登录成败指标
     */
    @Override
    public Mono<UserLoginVO> login(LoginDTO loginDTO) {
        return validateLoginCaptcha(loginDTO.getCaptchaId(), loginDTO.getCaptchaText())
            .then(findByUsername(loginDTO.getName())
                .switchIfEmpty(Mono.error(unauthorized(Messages.LOGIN))))
            .flatMap(user -> validatePassword(loginDTO.getPassword(), user).then(loginUser(user)))
            .flatMap(login -> imageCaptchaService.deleteCaptcha(loginDTO.getCaptchaId()).thenReturn(login))
            .doOnSuccess(ignored -> metricsRecorder.increment(MetricNames.USER_LOGIN, "result", "success"))
            .doOnError(ignored -> metricsRecorder.increment(MetricNames.USER_LOGIN, "result", "failure"));
    }

    /**
     * 同时校验图形验证码与邮箱验证码后按邮箱查找用户并创建登录会话
     */
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

    /**
     * 为用户创建令牌登录会话并回写最后登录时间
     */
    private Mono<UserLoginVO> loginUser(User user) {
        return tokenService.createLoginSession(user.getId(), user.getName())
            .flatMap(login -> markLastLoginTime(user).thenReturn(login));
    }

    /**
     * 校验用户存在后创建登录会话，将登录凭证JSON以随机票据键缓存进Redis，缓存失败时回收会话并报错
     */
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

    /**
     * 一次性兑换GitHub登录票据，读取并删除Redis中的凭证JSON后反序列化返回，票据过期或解析失败转为业务异常
     */
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
            .onErrorMap(error -> error instanceof BusinessException
                ? error
                : BusinessException.builder()
                    .httpStatus(HttpCode.INTERNAL_SERVER_ERROR)
                    .errorMessage(Messages.GITHUB_TOKEN_TICKET_PARSE_FAILED)
                    .cause(error).build());
    }

    /**
     * 校验邮箱未注册与验证码有效后加密密码创建本地用户，成功后标记邮箱已验证并记录注册指标
     */
    @Override
    public Mono<User> registerUser(UserRegisterDTO dto) {
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
            // 返回注册用户，便于上层把新增主键用于精确同步
            .flatMap(user -> emailVerificationService.markEmailAsVerified(dto.getEmail()).thenReturn(user))
            .doOnSuccess(ignored -> metricsRecorder.increment(MetricNames.USER_REGISTER, "result", "success"))
            .doOnError(ignored -> metricsRecorder.increment(MetricNames.USER_REGISTER, "result", "failure"));
    }

    /**
     * 无用户名过滤时从多级缓存读取全量非AI用户列表，否则按名称过滤查询
     */
    @Override
    public Mono<UserListVO> getAllUsers(String username) {
        if (!hasText(username)) {
            return getAllUsersFromCache();
        }
        return loadUsersByUsername(username);
    }

    /**
     * 读取全量非AI用户列表的多级缓存，未命中时回源数据库加载
     */
    private Mono<UserListVO> getAllUsersFromCache() {
        return cacheUtil.get(ALL_USERS_CACHE, RedisKeys.allUsersCache(), RedisKeys.allUsersCache(),
            UserListVO.class, this::loadAllUsers);
    }

    /**
     * 从仓储查询全部非AI用户并转换为VO组装为列表结果
     */
    private Mono<UserListVO> loadAllUsers() {
        return userRepository.findByRoleNotOrderByIdAsc(Defaults.AI_ROLE)
            .map(user -> BeanUtil.copyProperties(user, UserVO.class))
            .collectList()
            .map(records -> userList(records, records.size()));
    }

    /**
     * 按用户名模糊查询非AI用户并转换为VO组装为列表结果
     */
    private Mono<UserListVO> loadUsersByUsername(String username) {
        return userRepository.findByRoleNotAndNameContainingOrderByIdAsc(Defaults.AI_ROLE, username)
            .map(user -> BeanUtil.copyProperties(user, UserVO.class))
            .collectList()
            .map(records -> userList(records, records.size()));
    }

    /**
     * 查询全部AI角色用户并转换为VO组装为列表结果
     */
    @Override
    public Mono<UserListVO> getAllAiUsers() {
        return userRepository.findByRoleOrderByIdAsc(Defaults.AI_ROLE)
            .map(user -> BeanUtil.copyProperties(user, UserVO.class))
            .collectList()
            .map(records -> userList(records, records.size()));
    }

    /**
     * 查询非AI角色的用户ID的Flux流
     */
    @Override
    public Flux<Long> getNormalUserIds() {
        return userRepository.findIdsByRoleNot(Defaults.AI_ROLE);
    }

    /**
     * 查询AI角色用户的ID的Flux流
     */
    @Override
    public Flux<Long> getAiUserIds() {
        return userRepository.findIdsByRole(Defaults.AI_ROLE);
    }

    /**
     * 统计非AI角色用户数量并返回Mono响应式结果
     */
    @Override
    public Mono<Long> countNormalUsers() {
        return userRepository.countByRoleNot(Defaults.AI_ROLE);
    }

    /**
     * 统计AI角色用户数量并返回Mono响应式结果
     */
    @Override
    public Mono<Long> countAiUsers() {
        return userRepository.countByRole(Defaults.AI_ROLE);
    }

    /**
     * 事务保存用户，未加密的密码先加密，随后初始化登录状态并失效全量用户缓存
     */
    @Override
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

    /**
     * 从Redis读取用户状态键并转换为1在线0离线的登录状态
     */
    @Override
    public Mono<Integer> getUserLoginStatus(Long userId) {
        return redisUtil.get(RedisKeys.userStatus(userId)).map(status -> "1".equals(status) ? 1 : 0).defaultIfEmpty(0);
    }

    /**
     * 写入用户登录状态并失效全量用户列表缓存
     */
    @Override
    public Mono<Void> updateUserStatus(Long userId, String status) {
        return redisUtil.set(RedisKeys.userStatus(userId), status).then(evictAllUsersCache());
    }

    /**
     * 管理端创建本地用户，密码缺省时使用配置的默认密码并加密保存
     */
    @Override
    public Mono<User> createUser(UserCreateDTO dto) {
        User user = BeanUtil.copyProperties(dto, User.class);
        user.setRole("user");
        user.setAuthProvider("local");
        String rawPassword = hasText(user.getPassword())
            ? user.getPassword()
            : userPasswordProperties.defaultPassword();
        // 返回保存后的用户，便于上层把新增主键用于精确同步
        return encryptPassword(rawPassword)
            .flatMap(password -> {
                user.setPassword(password);
                return saveUserAndStatus(user);
            });
    }

    /**
     * 更新用户资料并保留GitHub信息与注册时间等受保护字段，填写新密码时重新加密，成功后失效相关缓存
     */
    @Override
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
            .then(Mono.when(evictAllUsersCache(), evictUserRoleCache(dto.getId().longValue())));
    }

    /**
     * 校验邮箱验证码后按邮箱定位用户并加密保存新密码
     */
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

    /**
     * 存在用户时将全部用户密码批量更新为配置的重置密码
     */
    @Override
    public Mono<Void> resetAllPasswords() {
        return userRepository.count()
            .filter(count -> count > 0)
            .switchIfEmpty(Mono.error(BusinessException.builder().httpStatus(HttpCode.UNPROCESSABLE_ENTITY)
                .errorMessage(Messages.PASSWORD_NO_USER).build()))
            .then(encryptPassword(userPasswordProperties.resetPassword()))
            .flatMap(userRepository::updateAllPasswords)
            .then();
    }

    /**
     * 定位指定用户后将密码重置为配置的重置密码并事务保存
     */
    @Override
    public Mono<Void> resetUserPassword(Long userId) {
        return userRepository.findById(userId)
            .switchIfEmpty(Mono.error(notFound(Messages.UNDEFINED_USER)))
            .flatMap(user -> encryptPassword(userPasswordProperties.resetPassword()).flatMap(password -> {
                user.setPassword(password);
                return transactionalOperator.transactional(userRepository.save(user));
            }))
            .then();
    }

    /**
     * 按GitHub ID查找用户并更新其GitHub资料与登录时间，不存在时以默认密码创建GitHub登录用户
     */
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
                return encryptPassword(userPasswordProperties.defaultPassword())
                    .flatMap(password -> {
                        newUser.setPassword(password);
                        return saveUserAndStatus(newUser);
                    })
                    .flatMap(saved -> evictAllUsersCache().thenReturn(saved));
            }));
    }

    /**
     * 用户角色为admin时判定为管理员，用户不存在时返回false
     */
    @Override
    public Mono<Boolean> isAdminUser(Long userId) {
        if (userId == null) {
            return Mono.just(false);
        }
        return userRepository.findById(userId)
            .map(user -> "admin".equalsIgnoreCase(user.getRole()))
            .defaultIfEmpty(false);
    }

    /**
     * 根据ID从仓储查询用户并返回Mono响应式结果
     */
    @Override
    public Mono<User> getById(Long id) {
        return userRepository.findById(id);
    }

    /**
     * 根据ID集合从仓储批量查询用户并返回Flux响应式流
     */
    @Override
    public Flux<User> listByIds(Collection<Long> ids) {
        return userRepository.findAllById(ids);
    }

    /**
     * 按更新时间增量或全量查询用户并转换为同步VO列表，用于Neo4j数据同步
     */
    @Override
    public Mono<List<UserSyncVO>> getNeo4jSyncUsers(String updatedAfter) {
        if (updatedAfter == null || updatedAfter.isBlank()) {
            return userRepository.findAll()
                .map(this::userToVO)
                .collectList()
                .map(list -> list.isEmpty() ? new ArrayList<>() : list);
        }
        LocalDateTime after = LocalDateTime.parse(updatedAfter);
        return userRepository.findByUpdateAtAfter(after)
            .map(this::userToVO)
            .collectList()
            .map(list -> list.isEmpty() ? new ArrayList<>() : list);
    }

    /**
     * 事务保存用户的最后登录时间并失效全量用户缓存
     */
    private Mono<Void> markLastLoginTime(User user) {
        user.setLastLoginAt(LocalDateTime.now());
        return transactionalOperator.transactional(userRepository.save(user))
            .then(evictAllUsersCache());
    }

    /**
     * 失效全量用户列表的多级缓存
     */
    private Mono<Void> evictAllUsersCache() {
        return cacheUtil.evict(RedisKeys.allUsersCache(), ALL_USERS_CACHE);
    }

    /**
     * 失效指定用户角色查询的多级缓存
     */
    private Mono<Void> evictUserRoleCache(Long userId) {
        return cacheUtil.evict(RedisKeys.userRole(userId), PermissionCheckerImpl.USER_ROLE_CACHE);
    }

    /**
     * 校验登录图形验证码，校验失败时抛出未授权业务异常
     */
    private Mono<Void> validateLoginCaptcha(String captchaId, String captchaText) {
        return imageCaptchaService.verifyCaptcha(captchaId, captchaText)
            .filter(Boolean.TRUE::equals)
            .switchIfEmpty(Mono.error(unauthorized(Messages.IMAGE_CAPTCHA_INVALID)))
            .then();
    }

    /**
     * 校验登录密码匹配，GitHub账号禁止密码登录，校验失败时抛出未授权业务异常
     */
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

    /**
     * 在弹性调度器上异步加密明文密码并返回Mono结果
     */
    private Mono<String> encryptPassword(String rawPassword) {
        return Mono.fromCallable(() -> passwordEncryptor.encryptPassword(rawPassword))
            .subscribeOn(Schedulers.boundedElastic());
    }

    /**
     * 以总数与用户列表构建分页列表VO
     */
    private UserListVO userList(List<UserVO> users, long total) {
        return UserListVO.builder().total(total).list(users).build();
    }

    /**
     * 判断字符串非null且非空白
     */
    private boolean hasText(String value) {
        return value != null && !value.isBlank();
    }

    /**
     * 通过BCrypt密文前缀判断密码是否已经过加密
     */
    private boolean isEncoded(String password) {
        return password != null && (password.startsWith("$2a$") || password.startsWith("$2b$")
            || password.startsWith("$2x$") || password.startsWith("$2y$"));
    }

    /**
     * 过滤null并去重，规范化ID列表
     */
    private List<Long> normalizeIds(List<Long> ids) {
        return ids == null ? List.of() : ids.stream().filter(id -> id != null).distinct().toList();
    }

    /**
     * 构建HTTP 404状态码的业务异常
     */
    private BusinessException notFound(String message) {
        return BusinessException.builder().httpStatus(HttpCode.NOT_FOUND).errorMessage(message).build();
    }

    /**
     * 构建HTTP 401状态码的业务异常
     */
    private BusinessException unauthorized(String message) {
        return BusinessException.builder().httpStatus(HttpCode.UNAUTHORIZED).errorMessage(message).build();
    }

    /**
     * 构建HTTP 409冲突状态码的业务异常
     */
    private BusinessException conflict(String message) {
        return BusinessException.builder().httpStatus(HttpCode.CONFLICT).errorMessage(message).build();
    }

    /**
     * 用户实体转 Map，字段名与数据库列名保持一致，用于 Neo4j 同步
     */
    private UserSyncVO userToVO(User user) {
        return new UserSyncVO(
            user.getId(),
            user.getName(),
            user.getEmail(),
            user.getRole(),
            user.getImg(),
            user.getSignature(),
            user.getCreateAt(),
            user.getUpdateAt());
    }
}

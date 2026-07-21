package com.hcsy.spring.api.service.impl;

import java.time.Duration;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.toolkit.Wrappers;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.hcsy.spring.api.mapper.UserMapper;
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

@Service
@RequiredArgsConstructor
public class UserServiceImpl extends ServiceImpl<UserMapper, User> implements UserService {
    private static final long GITHUB_TOKEN_TICKET_TTL_SECONDS = 60L;
    private static final String GITHUB_TOKEN_TICKET_PREFIX = "oauth:github:token:";
    private static final String ALL_USERS_CACHE_KEY = "user:page:all-users";
    private static final Duration CACHE_TTL = Duration.ofHours(24);

    private final UserMapper userMapper;
    private final RedisUtil redisUtil;
    private final TokenService tokenService;
    private final PasswordEncryptor passwordEncryptor;
    private final UserPasswordProperties userPasswordProperties;
    private final EmailVerificationService emailVerificationService;
    private final ImageCaptchaService imageCaptchaService;
    private final ObjectMapper objectMapper;
    private final SimpleLogger logger;

    @Transactional(readOnly = true)
    @SuppressWarnings("null")
    @Override
    public UserListVO listUsersWithFilter(long page, long size, String username) {
        // 1. 先获取所有符合条件的用户ID（轻量查询）
        LambdaQueryWrapper<User> idQueryWrapper = Wrappers.lambdaQuery();
        idQueryWrapper.select(User::getId);
        idQueryWrapper.ne(User::getRole, "ai");
        if (username != null && !username.isEmpty()) {
            idQueryWrapper.like(User::getName, username);
        }
        List<User> userIds = this.list(idQueryWrapper);

        if (userIds.isEmpty()) {
            return UserListVO.builder()
                    .total(0L)
                    .list(Collections.emptyList())
                    .build();
        }

        // 2. 批量从Redis获取所有用户的登录状态，构建 userId -> loginStatus 映射
        Map<Long, Integer> loginStatusMap = new HashMap<>();
        List<String> statusKeys = new ArrayList<>(userIds.size());
        for (User user : userIds) {
            statusKeys.add(RedisKeys.userStatus(user.getId()));
        }
        List<String> statuses = redisUtil.batchGet(statusKeys);
        for (int i = 0; i < userIds.size(); i++) {
            User user = userIds.get(i);
            String status = i < statuses.size() ? statuses.get(i) : null;
            int loginStatus = "1".equals(status) ? 1 : 0;
            loginStatusMap.put(user.getId(), loginStatus);
        }

        // 3. 使用自定义 Mapper 方法，在 SQL 层面完成排序和分页
        long offset = (page - 1) * size;
        List<User> users = userMapper.selectUsersWithLoginStatus(
                username,
                loginStatusMap,
                offset,
                size);

        // 4. 转换为 UserVO，设置登录状态和在线设备数
        List<UserVO> userVOs = new ArrayList<>();
        for (User user : users) {
            UserVO vo = BeanUtil.copyProperties(user, UserVO.class);
            vo.setLoginStatus(loginStatusMap.getOrDefault(user.getId(), 0));
            vo.setOnlineDeviceCount(tokenService.getUserOnlineDeviceCount(user.getId()));
            userVOs.add(vo);
        }

        // 5. 获取总数
        long total = userMapper.countUsersByUsername(username);

        // 6. 返回结果
        return UserListVO.builder()
                .total(total)
                .list(userVOs)
                .build();
    }

    @Override
    @Transactional
    @Neo4jSync(description = Messages.NEO4J_SYNC_DESC_USER_DELETE)
    public void deleteUserAndStatusById(Long id) {
        User existing = userMapper.selectById(id);
        if (existing == null) {
            throw BusinessException.builder().httpStatus(HttpCode.NOT_FOUND).errorMessage(Messages.UNDEFINED_USER).build();
        }
        userMapper.deleteById(id);
        evictAllUsersCache();
        redisUtil.delete(RedisKeys.userStatus(id));
    }

    @Override
    @Transactional
    @Neo4jSync(description = Messages.NEO4J_SYNC_DESC_USER_BATCH_DELETE)
    public void deleteUsersAndStatusByIds(List<Long> ids) {
        if (ids == null || ids.isEmpty())
            return;

        List<Long> distinctIds = ids.stream()
                .filter(id -> id != null)
                .distinct()
                .toList();
        if (distinctIds.isEmpty()) {
            return;
        }

        // 批量删除前校验：必须全部存在（只要有一个不存在就抛异常）
        List<User> existingList = userMapper.selectBatchIds(distinctIds);
        if (existingList.size() != distinctIds.size()) {
            throw BusinessException.builder().httpStatus(HttpCode.NOT_FOUND).errorMessage(Messages.UNDEFINED_USERS).build();
        }

        userMapper.deleteBatchIds(ids);
        evictAllUsersCache();
        for (Long id : ids) {
            redisUtil.delete(RedisKeys.userStatus(id));
        }
    }

    @Transactional(readOnly = true)
    @SuppressWarnings("null")
    @Override
    public User findByUsername(String username) {
        LambdaQueryWrapper<User> queryWrapper = Wrappers.lambdaQuery();
        if (username != null && !username.isEmpty()) {
            queryWrapper.eq(User::getName, username);
        }
        return userMapper.selectOne(queryWrapper);
    }

    @Transactional(readOnly = true)
    @SuppressWarnings("null")
    @Override
    public List<User> listAllUserByUsername(String username) {
        LambdaQueryWrapper<User> queryWrapper = Wrappers.lambdaQuery();
        if (username != null && !username.isEmpty()) {
            queryWrapper.like(User::getName, username);
        }
        return userMapper.selectList(queryWrapper);
    }

    @Override
    public UserLoginVO login(LoginDTO loginDTO) {
        validateLoginCaptcha(loginDTO.getCaptchaId(), loginDTO.getCaptchaText());

        User user = findByUsername(loginDTO.getName());
        if (user == null) {
            throw BusinessException.builder().httpStatus(HttpCode.UNAUTHORIZED).errorMessage(Messages.LOGIN).build();
        }
        if ("github".equalsIgnoreCase(user.getAuthProvider())
                && Defaults.HIDE_PASSWORD.equals(user.getPassword())) {
            throw BusinessException.builder().httpStatus(HttpCode.UNAUTHORIZED).errorMessage(Messages.GITHUB_ACCOUNT_PASSWORD_LOGIN_BLOCKED).build();
        }
        if (!passwordEncryptor.matchPassword(loginDTO.getPassword(), user.getPassword())) {
            throw BusinessException.builder().httpStatus(HttpCode.UNAUTHORIZED).errorMessage(Messages.LOGIN).build();
        }

        UserLoginVO loginVO = tokenService.createLoginSession(user.getId(), user.getName());
        markLastLoginTime(user);
        imageCaptchaService.deleteCaptcha(loginDTO.getCaptchaId());
        return loginVO;
    }

    @Override
    public UserLoginVO emailLogin(EmailLoginDTO emailLoginDTO) {
        validateLoginCaptcha(emailLoginDTO.getCaptchaId(), emailLoginDTO.getCaptchaText());

        if (!emailVerificationService.verifyCode(emailLoginDTO.getEmail(), emailLoginDTO.getVerificationCode())) {
            throw BusinessException.builder().httpStatus(HttpCode.UNAUTHORIZED).errorMessage(Messages.VERIFY_CODE).build();
        }

        User user = findByEmail(emailLoginDTO.getEmail());
        if (user == null) {
            throw BusinessException.builder().httpStatus(HttpCode.NOT_FOUND).errorMessage(Messages.UNDEFINED_USER_REGISTER).build();
        }

        UserLoginVO loginVO = tokenService.createLoginSession(user.getId(), user.getName());
        markLastLoginTime(user);
        imageCaptchaService.deleteCaptcha(emailLoginDTO.getCaptchaId());
        return loginVO;
    }

    @Override
    public GithubTokenTicketVO createGithubTokenTicket(GithubTokenTicketCreateDTO dto) {
        User user = getById(dto.getUserId());
        if (user == null) {
            throw BusinessException.builder().httpStatus(HttpCode.NOT_FOUND).errorMessage(Messages.UNDEFINED_USER).build();
        }

        UserLoginVO loginVO = tokenService.createLoginSession(user.getId(), user.getName());
        String ticket = UUID.randomUUID().toString().replace("-", "");

        try {
            redisUtil.set(
                    buildGithubTicketKey(ticket),
                    objectMapper.writeValueAsString(loginVO),
                    GITHUB_TOKEN_TICKET_TTL_SECONDS);
        evictAllUsersCache();
        } catch (Exception e) {
            try {
                tokenService.removeSessionByAccessToken(loginVO.getAccessToken());
            } catch (Exception cleanupError) {
                // 清理失败不影响主异常返回，避免掩盖真实错误
            }
            throw BusinessException.builder().httpStatus(HttpCode.INTERNAL_SERVER_ERROR).errorMessage(Messages.GITHUB_LOGIN_TICKET_CACHE_FAILED).cause(e).build();
        }

        return GithubTokenTicketVO.builder()
                .ticket(ticket)
                .expiresIn(GITHUB_TOKEN_TICKET_TTL_SECONDS)
                .build();
    }

    @Override
    public UserLoginVO exchangeGithubTokenTicket(GithubTokenExchangeDTO dto) {
        String ticket = dto.getTicket() == null ? null : dto.getTicket().trim();
        if (ticket == null || ticket.isEmpty()) {
            throw BusinessException.builder().httpStatus(HttpCode.BAD_REQUEST).errorMessage(Messages.GITHUB_TOKEN_TICKET_EMPTY).build();
        }

        String ticketKey = buildGithubTicketKey(ticket);
        String storedValue = redisUtil.get(ticketKey);
        if (storedValue == null) {
            throw BusinessException.builder().httpStatus(HttpCode.UNAUTHORIZED).errorMessage(Messages.GITHUB_TOKEN_TICKET_EXPIRED).build();
        }

        redisUtil.delete(ticketKey);

        try {
            return objectMapper.readValue(storedValue, UserLoginVO.class);
        } catch (Exception e) {
            throw BusinessException.builder().httpStatus(HttpCode.INTERNAL_SERVER_ERROR).errorMessage(Messages.GITHUB_TOKEN_TICKET_PARSE_FAILED).cause(e).build();
        }
    }

    @Override
    public void registerUser(UserRegisterDTO registerDTO) {
        User existingUser = findByEmail(registerDTO.getEmail());
        if (existingUser != null) {
            throw BusinessException.builder().httpStatus(HttpCode.CONFLICT).errorMessage(Messages.EMAIL_REGISTER).build();
        }

        if (!emailVerificationService.verifyCode(registerDTO.getEmail(), registerDTO.getVerificationCode())) {
            throw BusinessException.builder().httpStatus(HttpCode.UNAUTHORIZED).errorMessage(Messages.VERIFY_CODE).build();
        }

        User user = BeanUtil.copyProperties(registerDTO, User.class);
        user.setRole("user");
        user.setAuthProvider("local");
        user.setPassword(passwordEncryptor.encryptPassword(user.getPassword()));
        saveUserAndStatus(user);

        emailVerificationService.markEmailAsVerified(registerDTO.getEmail());
        evictAllUsersCache();
    }

    @Transactional(readOnly = true)
    @SuppressWarnings("null")
    @Override
    public UserListVO getAllUsers(String username) {
        // 只有不带搜索条件的全量查询才使用缓存
        boolean useCache = (username == null || username.isEmpty());
        if (useCache) {
            try {
                String cached = redisUtil.get(ALL_USERS_CACHE_KEY);
                if (cached != null && !cached.isEmpty()) {
                    return objectMapper.readValue(cached, UserListVO.class);
                }
            } catch (Exception e) {
                logger.error("用户列表缓存读取失败: " + e.getMessage());
            }
        }

        long total = userMapper.countUsersByUsername(username);

        if (total == 0) {
            UserListVO emptyResult = UserListVO.builder()
                    .total(0L)
                    .list(Collections.emptyList())
                    .build();
            if (useCache) {
                try {
                    String json = objectMapper.writeValueAsString(emptyResult);
                    redisUtil.set(ALL_USERS_CACHE_KEY, json, 10 * 60L);
                } catch (Exception e) {
                    logger.error("用户列表缓存写入失败: " + e.getMessage());
                }
            }
            return emptyResult;
        }

        LambdaQueryWrapper<User> queryWrapper = Wrappers.lambdaQuery();
        queryWrapper.ne(User::getRole, "ai");
        if (username != null && !username.isEmpty()) {
            queryWrapper.like(User::getName, username);
        }
        List<User> users = this.list(queryWrapper);

        List<UserVO> voList = users.stream().map(user -> {
            UserVO vo = new UserVO();
            BeanUtil.copyProperties(user, vo);
            return vo;
        }).toList();

        UserListVO result = UserListVO.builder()
                .total(total)
                .list(voList)
                .build();

        if (useCache) {
            try {
                String json = objectMapper.writeValueAsString(result);
                redisUtil.set(ALL_USERS_CACHE_KEY, json, CACHE_TTL.toSeconds());
            } catch (Exception e) {
                logger.error("用户列表缓存写入失败: " + e.getMessage());
            }
        }

        return result;
    }

    @Transactional(readOnly = true)
    @SuppressWarnings("null")
    @Override
    public UserListVO getAllAiUsers() {
        long total = userMapper.countAiUsers();

        if (total == 0) {
            return UserListVO.builder()
                    .total(0L)
                    .list(Collections.emptyList())
                    .build();
        }

        LambdaQueryWrapper<User> queryWrapper = Wrappers.lambdaQuery();
        queryWrapper.eq(User::getRole, "ai");
        List<User> users = this.list(queryWrapper);

        List<UserVO> voList = users.stream().map(user -> {
            UserVO vo = new UserVO();
            BeanUtil.copyProperties(user, vo);
            return vo;
        }).toList();

        return UserListVO.builder()
                .total(total)
                .list(voList)
                .build();
    }

    @Transactional(readOnly = true)
    @Override
    public List<Long> getNormalUserIds() {
        return userMapper.selectNormalUserIds();
    }

    @Transactional(readOnly = true)
    @Override
    public List<Long> getAiUserIds() {
        return userMapper.selectAiUserIds();
    }

    @Transactional(readOnly = true)
    @Override
    public long countNormalUsers() {
        return userMapper.countNormalUsers();
    }

    @Transactional(readOnly = true)
    @Override
    public long countAiUsers() {
        return userMapper.countAiUsers();
    }

    @Override
    @Neo4jSync(description = Messages.NEO4J_SYNC_DESC_USER_SAVE)
    public void saveUserAndStatus(User user) {
        if (user.getAuthProvider() == null || user.getAuthProvider().isBlank()) {
            user.setAuthProvider("local");
        }
        String password = user.getPassword();
        if (password != null && !password.isEmpty()) {
            if (!password.startsWith("$2a$") && !password.startsWith("$2b$") && !password.startsWith("$2x$")
                    && !password.startsWith("$2y$")) {
                user.setPassword(passwordEncryptor.encryptPassword(password));
            }
        }
        this.save(user);
        redisUtil.set(RedisKeys.userStatus(user.getId()), "0");
    }

    @Transactional(readOnly = true)
    @SuppressWarnings("null")
    @Override
    public User findByEmail(String email) {
        LambdaQueryWrapper<User> queryWrapper = Wrappers.lambdaQuery();
        queryWrapper.eq(User::getEmail, email);
        return this.getOne(queryWrapper);
    }

    @Override
    public int getUserLoginStatus(Long userId) {
        String status = redisUtil.get(RedisKeys.userStatus(userId));
        return "1".equals(status) ? 1 : 0;
    }

    @Override
    public void updateUserStatus(Long userId, String status) {
        redisUtil.set(RedisKeys.userStatus(userId), status);
        evictAllUsersCache();
    }

    @Override
    @Transactional
    @Neo4jSync(description = Messages.NEO4J_SYNC_DESC_USER_SAVE)
    public void createUser(UserCreateDTO userDto) {
        User user = BeanUtil.copyProperties(userDto, User.class);
        user.setRole("user");
        user.setAuthProvider("local");
        if (user.getPassword() == null || user.getPassword().isBlank()) {
            user.setPassword(userPasswordProperties.getDefaultPassword());
        } else {
            user.setPassword(passwordEncryptor.encryptPassword(user.getPassword()));
        }
        saveUserAndStatus(user);
        evictAllUsersCache();
    }

    @Override
    @Transactional
    @Neo4jSync(description = Messages.NEO4J_SYNC_DESC_USER_UPDATE)
    public void updateUserInfo(UserUpdateDTO userDto) {
        User existingUser = getById(userDto.getId());
        if (existingUser == null) {
            throw BusinessException.builder().httpStatus(HttpCode.NOT_FOUND).errorMessage(Messages.UNDEFINED_USER).build();
        }

        User user = BeanUtil.copyProperties(userDto, User.class);
        user.setGithubId(existingUser.getGithubId());
        user.setGithubLogin(existingUser.getGithubLogin());
        user.setGithubUrl(existingUser.getGithubUrl());
        user.setAuthProvider(existingUser.getAuthProvider());
        user.setLastLoginAt(existingUser.getLastLoginAt());

        if (userDto.getPassword() == null || userDto.getPassword().isBlank()) {
            user.setPassword(existingUser.getPassword());
        } else {
            user.setPassword(passwordEncryptor.encryptPassword(userDto.getPassword()));
        }

        updateById(user);
        evictAllUsersCache();
    }

    @Override
    @Transactional
    public void resetPassword(ResetPasswordDTO resetPasswordDTO) {
        if (!emailVerificationService.verifyCode(resetPasswordDTO.getEmail(),
                resetPasswordDTO.getVerificationCode())) {
            throw BusinessException.builder().httpStatus(HttpCode.UNAUTHORIZED).errorMessage(Messages.VERIFY_CODE).build();
        }

        User user = findByEmail(resetPasswordDTO.getEmail());
        if (user == null) {
            throw BusinessException.builder().httpStatus(HttpCode.NOT_FOUND).errorMessage(Messages.UNDEFINED_USER).build();
        }

        user.setPassword(passwordEncryptor.encryptPassword(resetPasswordDTO.getNewPassword()));
        updateById(user);
    }

    @Override
    @Transactional
    public void resetAllPasswords() {
        List<User> allUsers = list();
        if (allUsers == null || allUsers.isEmpty()) {
            throw BusinessException.builder().httpStatus(HttpCode.UNPROCESSABLE_ENTITY).errorMessage(Messages.PASSWORD_NO_USER).build();
        }

        final String resetPassword = passwordEncryptor.encryptPassword(userPasswordProperties.getResetPassword());
        allUsers.forEach(user -> user.setPassword(resetPassword));
        updateBatchById(allUsers);
    }

    @Override
    @Transactional
    public void resetUserPassword(Long userId) {
        User user = getById(userId);
        if (user == null) {
            throw BusinessException.builder().httpStatus(HttpCode.NOT_FOUND).errorMessage(Messages.UNDEFINED_USER).build();
        }

        final String resetPassword = passwordEncryptor.encryptPassword(userPasswordProperties.getResetPassword());
        user.setPassword(resetPassword);
        updateById(user);
    }

    /**
     * 清除所有用户列表缓存，在任何修改用户的操作后调用
     */
    private void evictAllUsersCache() {
        try {
            redisUtil.delete(ALL_USERS_CACHE_KEY);
        } catch (Exception e) {
            logger.error("用户列表缓存清除失败: " + e.getMessage());
        }
    }

    private void validateLoginCaptcha(String captchaId, String captchaText) {
        if (!imageCaptchaService.verifyCaptcha(captchaId, captchaText)) {
            throw BusinessException.builder().httpStatus(HttpCode.UNAUTHORIZED).errorMessage(Messages.IMAGE_CAPTCHA_INVALID).build();
        }
    }

    private void markLastLoginTime(User user) {
        user.setLastLoginAt(LocalDateTime.now());
        this.updateById(user);
    }

    private String buildGithubTicketKey(String ticket) {
        return GITHUB_TOKEN_TICKET_PREFIX + ticket;
    }
}

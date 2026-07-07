package com.hcsy.spring.api.service.impl;

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
import com.hcsy.spring.common.exceptions.BusinessException;
import com.hcsy.spring.common.utils.Constants;
import com.hcsy.spring.common.utils.HttpCode;
import com.hcsy.spring.common.utils.PasswordEncryptor;
import com.hcsy.spring.common.utils.RedisKeys;
import com.hcsy.spring.common.utils.RedisUtil;
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

    private final UserMapper userMapper;
    private final RedisUtil redisUtil;
    private final TokenService tokenService;
    private final PasswordEncryptor passwordEncryptor;
    private final UserPasswordProperties userPasswordProperties;
    private final EmailVerificationService emailVerificationService;
    private final ImageCaptchaService imageCaptchaService;
    private final ObjectMapper objectMapper;

    @SuppressWarnings("null")
    @Override
    public UserListVO listUsersWithFilter(long page, long size, String username) {
        // 1. 先获取所有符合条件的用户ID（轻量查询）
        LambdaQueryWrapper<User> idQueryWrapper = Wrappers.lambdaQuery();
        idQueryWrapper.select(User::getId);
        // 排除 role 为 ai 的用户
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
        List<UserVO> userVOs = new java.util.ArrayList<>();
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
    @Neo4jSync(description = Constants.NEO4J_SYNC_DESC_USER_DELETE)
    public void deleteUserAndStatusById(Long id) {
        User existing = userMapper.selectById(id);
        if (existing == null) {
            throw BusinessException.builder().httpStatus(HttpCode.NOT_FOUND).errorMessage(Constants.UNDEFINED_USER).build();
        }
        userMapper.deleteById(id);
        redisUtil.delete(RedisKeys.userStatus(id));
    }

    @Override
    @Transactional
    @Neo4jSync(description = Constants.NEO4J_SYNC_DESC_USER_BATCH_DELETE)
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
            throw BusinessException.builder().httpStatus(HttpCode.NOT_FOUND).errorMessage(Constants.UNDEFINED_USERS).build();
        }

        userMapper.deleteBatchIds(ids);
        for (Long id : ids) {
            redisUtil.delete(RedisKeys.userStatus(id));
        }
    }

    @SuppressWarnings("null")
    @Override
    public User findByUsername(String username) {
        LambdaQueryWrapper<User> queryWrapper = Wrappers.lambdaQuery();
        if (username != null && !username.isEmpty()) {
            queryWrapper.eq(User::getName, username); // 用户名模糊匹配
        }
        return userMapper.selectOne(queryWrapper);
    }

    @SuppressWarnings("null")
    @Override
    public List<User> listAllUserByUsername(String username) {
        LambdaQueryWrapper<User> queryWrapper = Wrappers.lambdaQuery();
        if (username != null && !username.isEmpty()) {
            queryWrapper.like(User::getName, username); // 用户名模糊匹配
        }
        return userMapper.selectList(queryWrapper);
    }

    @Override
    public UserLoginVO login(LoginDTO loginDTO) {
        validateLoginCaptcha(loginDTO.getCaptchaId(), loginDTO.getCaptchaText());

        User user = findByUsername(loginDTO.getName());
        if (user == null) {
            throw BusinessException.builder().httpStatus(HttpCode.UNAUTHORIZED).errorMessage(Constants.LOGIN).build();
        }
        if ("github".equalsIgnoreCase(user.getAuthProvider())
                && Constants.HIDE_PASSWORD.equals(user.getPassword())) {
            throw BusinessException.builder().httpStatus(HttpCode.UNAUTHORIZED).errorMessage(Constants.GITHUB_ACCOUNT_PASSWORD_LOGIN_BLOCKED).build();
        }
        if (!passwordEncryptor.matchPassword(loginDTO.getPassword(), user.getPassword())) {
            throw BusinessException.builder().httpStatus(HttpCode.UNAUTHORIZED).errorMessage(Constants.LOGIN).build();
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
            throw BusinessException.builder().httpStatus(HttpCode.UNAUTHORIZED).errorMessage(Constants.VERIFY_CODE).build();
        }

        User user = findByEmail(emailLoginDTO.getEmail());
        if (user == null) {
            throw BusinessException.builder().httpStatus(HttpCode.NOT_FOUND).errorMessage(Constants.UNDEFINED_USER_REGISTER).build();
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
            throw BusinessException.builder().httpStatus(HttpCode.NOT_FOUND).errorMessage(Constants.UNDEFINED_USER).build();
        }

        UserLoginVO loginVO = tokenService.createLoginSession(user.getId(), user.getName());
        String ticket = UUID.randomUUID().toString().replace("-", "");

        try {
            redisUtil.set(
                    buildGithubTicketKey(ticket),
                    objectMapper.writeValueAsString(loginVO),
                    GITHUB_TOKEN_TICKET_TTL_SECONDS);
        } catch (Exception e) {
            try {
                tokenService.removeSessionByAccessToken(loginVO.getAccessToken());
            } catch (Exception cleanupError) {
                // 清理失败不影响主异常返回，避免掩盖真实错误
            }
            throw BusinessException.builder().httpStatus(HttpCode.INTERNAL_SERVER_ERROR).errorMessage(Constants.GITHUB_LOGIN_TICKET_CACHE_FAILED).cause(e).build();
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
            throw BusinessException.builder().httpStatus(HttpCode.BAD_REQUEST).errorMessage(Constants.GITHUB_TOKEN_TICKET_EMPTY).build();
        }

        String ticketKey = buildGithubTicketKey(ticket);
        String storedValue = redisUtil.get(ticketKey);
        if (storedValue == null) {
            throw BusinessException.builder().httpStatus(HttpCode.UNAUTHORIZED).errorMessage(Constants.GITHUB_TOKEN_TICKET_EXPIRED).build();
        }

        redisUtil.delete(ticketKey);

        try {
            return objectMapper.readValue(storedValue, UserLoginVO.class);
        } catch (Exception e) {
            throw BusinessException.builder().httpStatus(HttpCode.INTERNAL_SERVER_ERROR).errorMessage(Constants.GITHUB_TOKEN_TICKET_PARSE_FAILED).cause(e).build();
        }
    }

    @Override
    public void registerUser(UserRegisterDTO registerDTO) {
        User existingUser = findByEmail(registerDTO.getEmail());
        if (existingUser != null) {
            throw BusinessException.builder().httpStatus(HttpCode.CONFLICT).errorMessage(Constants.EMAIL_REGISTER).build();
        }

        if (!emailVerificationService.verifyCode(registerDTO.getEmail(), registerDTO.getVerificationCode())) {
            throw BusinessException.builder().httpStatus(HttpCode.UNAUTHORIZED).errorMessage(Constants.VERIFY_CODE).build();
        }

        User user = BeanUtil.copyProperties(registerDTO, User.class);
        user.setRole("user");
        user.setAuthProvider("local");
        user.setPassword(passwordEncryptor.encryptPassword(user.getPassword()));
        saveUserAndStatus(user);

        emailVerificationService.markEmailAsVerified(registerDTO.getEmail());
    }

    @SuppressWarnings("null")
    @Override
    public UserListVO getAllUsers(String username) {
        // 先通过 SQL COUNT 获取总数，避免内存中 list.size()
        long total = userMapper.countUsersByUsername(username);

        if (total == 0) {
            return UserListVO.builder()
                    .total(0L)
                    .list(Collections.emptyList())
                    .build();
        }

        // 查询所有符合条件的用户
        LambdaQueryWrapper<User> queryWrapper = Wrappers.lambdaQuery();
        queryWrapper.ne(User::getRole, "ai"); // 排除 role 为 ai 的用户
        if (username != null && !username.isEmpty()) {
            queryWrapper.like(User::getName, username);
        }
        List<User> users = this.list(queryWrapper);

        // 转换为 UserVO（不包含登录状态和设备数）
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

    @SuppressWarnings("null")
    @Override
    public UserListVO getAllAiUsers() {
        // 先通过 SQL COUNT 获取总数，避免内存中 list.size()
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

    @Override
    public List<Long> getNormalUserIds() {
        return userMapper.selectNormalUserIds();
    }

    @Override
    public List<Long> getAiUserIds() {
        return userMapper.selectAiUserIds();
    }

    @Override
    public long countNormalUsers() {
        return userMapper.countNormalUsers();
    }

    @Override
    public long countAiUsers() {
        return userMapper.countAiUsers();
    }

    @Override
    @Neo4jSync(description = Constants.NEO4J_SYNC_DESC_USER_SAVE)
    public void saveUserAndStatus(User user) {
        // 加密密码后再保存
        if (user.getAuthProvider() == null || user.getAuthProvider().isBlank()) {
            user.setAuthProvider("local");
        }
        String password = user.getPassword();
        if (password != null && !password.isEmpty()) {
            // 检查是否已经被加密过（bcrypt hash 格式为 $2a$, $2b$, $2x$, $2y$ 开头）
            if (!password.startsWith("$2a$") && !password.startsWith("$2b$") && !password.startsWith("$2x$")
                    && !password.startsWith("$2y$")) {
                user.setPassword(passwordEncryptor.encryptPassword(password));
            }
        }
        this.save(user);
        redisUtil.set(RedisKeys.userStatus(user.getId()), "0");
    }

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
    }

    @Override
    @Transactional
    @Neo4jSync(description = Constants.NEO4J_SYNC_DESC_USER_SAVE)
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
    }

    @Override
    @Transactional
    @Neo4jSync(description = Constants.NEO4J_SYNC_DESC_USER_UPDATE)
    public void updateUserInfo(UserUpdateDTO userDto) {
        User existingUser = getById(userDto.getId());
        if (existingUser == null) {
            throw BusinessException.builder().httpStatus(HttpCode.NOT_FOUND).errorMessage(Constants.UNDEFINED_USER).build();
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
    }

    @Override
    @Transactional
    public void resetPassword(ResetPasswordDTO resetPasswordDTO) {
        if (!emailVerificationService.verifyCode(resetPasswordDTO.getEmail(),
                resetPasswordDTO.getVerificationCode())) {
            throw BusinessException.builder().httpStatus(HttpCode.UNAUTHORIZED).errorMessage(Constants.VERIFY_CODE).build();
        }

        User user = findByEmail(resetPasswordDTO.getEmail());
        if (user == null) {
            throw BusinessException.builder().httpStatus(HttpCode.NOT_FOUND).errorMessage(Constants.UNDEFINED_USER).build();
        }

        user.setPassword(passwordEncryptor.encryptPassword(resetPasswordDTO.getNewPassword()));
        updateById(user);
    }

    @Override
    @Transactional
    public void resetAllPasswords() {
        List<User> allUsers = list();
        if (allUsers == null || allUsers.isEmpty()) {
            throw BusinessException.builder().httpStatus(HttpCode.UNPROCESSABLE_ENTITY).errorMessage(Constants.PASSWORD_NO_USER).build();
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
            throw BusinessException.builder().httpStatus(HttpCode.NOT_FOUND).errorMessage(Constants.UNDEFINED_USER).build();
        }

        final String resetPassword = passwordEncryptor.encryptPassword(userPasswordProperties.getResetPassword());
        user.setPassword(resetPassword);
        updateById(user);
    }

    private void validateLoginCaptcha(String captchaId, String captchaText) {
        if (!imageCaptchaService.verifyCaptcha(captchaId, captchaText)) {
            throw BusinessException.builder().httpStatus(HttpCode.UNAUTHORIZED).errorMessage(Constants.IMAGE_CAPTCHA_INVALID).build();
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

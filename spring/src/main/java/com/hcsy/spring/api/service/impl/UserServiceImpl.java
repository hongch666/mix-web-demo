package com.hcsy.spring.api.service.impl;

import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.toolkit.Wrappers;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.hcsy.spring.api.mapper.UserMapper;
import com.hcsy.spring.api.service.EmailVerificationService;
import com.hcsy.spring.api.service.TokenService;
import com.hcsy.spring.api.service.UserService;
import com.hcsy.spring.common.exceptions.BusinessException;
import com.hcsy.spring.common.utils.Constants;
import com.hcsy.spring.common.utils.JwtUtil;
import com.hcsy.spring.common.utils.PasswordEncryptor;
import com.hcsy.spring.common.utils.RedisUtil;
import com.hcsy.spring.entity.dto.EmailLoginDTO;
import com.hcsy.spring.entity.dto.LoginDTO;
import com.hcsy.spring.entity.dto.UserRegisterDTO;
import com.hcsy.spring.entity.po.User;
import com.hcsy.spring.entity.vo.UserListVO;
import com.hcsy.spring.entity.vo.UserLoginVO;
import com.hcsy.spring.entity.vo.UserVO;

import cn.hutool.core.bean.BeanUtil;
import lombok.RequiredArgsConstructor;

@Service
@RequiredArgsConstructor
public class UserServiceImpl extends ServiceImpl<UserMapper, User> implements UserService {
    private final UserMapper userMapper;
    private final RedisUtil redisUtil;
    private final TokenService tokenService;
    private final PasswordEncryptor passwordEncryptor;
    private final JwtUtil jwtUtil;
    private final EmailVerificationService emailVerificationService;

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
            statusKeys.add("user:status:" + user.getId());
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
    public void deleteUserAndStatusById(Long id) {
        User existing = userMapper.selectById(id);
        if (existing == null) {
            throw new BusinessException(Constants.UNDEFINED_USER);
        }
        userMapper.deleteById(id);
        redisUtil.delete("user:status:" + id);
    }

    @Override
    @Transactional
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
            throw new BusinessException(Constants.UNDEFINED_USERS);
        }

        userMapper.deleteBatchIds(ids);
        for (Long id : ids) {
            redisUtil.delete("user:status:" + id);
        }
    }

    @Override
    public User findByUsername(String username) {
        LambdaQueryWrapper<User> queryWrapper = Wrappers.lambdaQuery();
        if (username != null && !username.isEmpty()) {
            queryWrapper.eq(User::getName, username); // 用户名模糊匹配
        }
        return userMapper.selectOne(queryWrapper);
    }

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
        User user = findByUsername(loginDTO.getName());
        if (user == null || !passwordEncryptor.matchPassword(loginDTO.getPassword(), user.getPassword())) {
            throw new BusinessException(Constants.LOGIN);
        }
        return buildLoginVO(user);
    }

    @Override
    public UserLoginVO emailLogin(EmailLoginDTO emailLoginDTO) {
        if (!emailVerificationService.verifyCode(emailLoginDTO.getEmail(), emailLoginDTO.getVerificationCode())) {
            throw new BusinessException(Constants.VERIFY_CODE);
        }

        User user = findByEmail(emailLoginDTO.getEmail());
        if (user == null) {
            throw new BusinessException(Constants.UNDEFINED_USER_REGISTER);
        }

        return buildLoginVO(user);
    }

    @Override
    public void registerUser(UserRegisterDTO registerDTO) {
        User existingUser = findByEmail(registerDTO.getEmail());
        if (existingUser != null) {
            throw new BusinessException(Constants.EMAIL_REGISTER);
        }

        if (!emailVerificationService.verifyCode(registerDTO.getEmail(), registerDTO.getVerificationCode())) {
            throw new BusinessException(Constants.VERIFY_CODE);
        }

        User user = BeanUtil.copyProperties(registerDTO, User.class);
        user.setRole("user");
        user.setPassword(passwordEncryptor.encryptPassword(user.getPassword()));
        saveUserAndStatus(user);

        emailVerificationService.markEmailAsVerified(registerDTO.getEmail());
    }

    @Override
    public UserListVO getAllUsers(String username) {
        // 查询所有符合条件的用户
        LambdaQueryWrapper<User> queryWrapper = Wrappers.lambdaQuery();
        queryWrapper.ne(User::getRole, "ai"); // 排除 role 为 ai 的用户
        if (username != null && !username.isEmpty()) {
            queryWrapper.like(User::getName, username);
        }
        List<User> users = this.list(queryWrapper);

        if (users.isEmpty()) {
            return UserListVO.builder()
                    .total(0L)
                    .list(Collections.emptyList())
                    .build();
        }

        // 转换为 UserVO（不包含登录状态和设备数）
        List<UserVO> voList = users.stream().map(user -> {
            UserVO vo = new UserVO();
            BeanUtil.copyProperties(user, vo);
            return vo;
        }).toList();

        return UserListVO.builder()
                .total((long) users.size())
                .list(voList)
                .build();
    }

    @Override
    public void saveUserAndStatus(User user) {
        // 加密密码后再保存
        String password = user.getPassword();
        if (password != null && !password.isEmpty()) {
            // 检查是否已经被加密过（bcrypt hash 格式为 $2a$, $2b$, $2x$, $2y$ 开头）
            if (!password.startsWith("$2a$") && !password.startsWith("$2b$") && !password.startsWith("$2x$")
                    && !password.startsWith("$2y$")) {
                user.setPassword(passwordEncryptor.encryptPassword(password));
            }
        }
        this.save(user);
        redisUtil.set("user:status:" + user.getId(), "0");
    }

    @Override
    public User findByEmail(String email) {
        LambdaQueryWrapper<User> queryWrapper = Wrappers.lambdaQuery();
        queryWrapper.eq(User::getEmail, email);
        return this.getOne(queryWrapper);
    }

    private UserLoginVO buildLoginVO(User user) {
        String token = jwtUtil.generateToken(user.getId(), user.getName());
        tokenService.saveToken(user.getId(), token);

        return UserLoginVO.builder()
                .token(token)
                .userId(user.getId())
                .username(user.getName())
                .onlineDeviceCount(tokenService.getUserOnlineDeviceCount(user.getId()))
                .build();
    }
}

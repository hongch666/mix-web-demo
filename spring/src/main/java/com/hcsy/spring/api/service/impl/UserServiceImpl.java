package com.hcsy.spring.api.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.toolkit.Wrappers;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;

import lombok.RequiredArgsConstructor;

import com.hcsy.spring.api.mapper.UserMapper;
import com.hcsy.spring.api.service.UserService;
import com.hcsy.spring.api.service.TokenService;
import com.hcsy.spring.common.utils.RedisUtil;
import com.hcsy.spring.entity.po.User;
import com.hcsy.spring.entity.vo.UserVO;

import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import cn.hutool.core.bean.BeanUtil;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@RequiredArgsConstructor
@Transactional
public class UserServiceImpl extends ServiceImpl<UserMapper, User> implements UserService {
    private final UserMapper userMapper;
    private final RedisUtil redisUtil;
    private final TokenService tokenService;

    @Override
    public Map<String, Object> listUsersWithFilter(long page, long size, String username) {
        Map<String, Object> result = new HashMap<>();

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
            result.put("total", 0L);
            result.put("list", Collections.emptyList());
            return result;
        }

        // 2. 批量从Redis获取所有用户的登录状态，构建 userId -> loginStatus 映射
        Map<Long, Integer> loginStatusMap = new HashMap<>();
        for (User user : userIds) {
            String status = (String) redisUtil.get("user:status:" + user.getId());
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
        result.put("total", total);
        result.put("list", userVOs);
        return result;
    }

    @Transactional
    public void deleteUserAndStatusById(Long id) {
        userMapper.deleteById(id);
        redisUtil.delete("user:status:" + id);
    }

    @Transactional
    public void deleteUsersAndStatusByIds(List<Long> ids) {
        if (ids == null || ids.isEmpty())
            return;
        userMapper.deleteBatchIds(ids);
        for (Long id : ids) {
            redisUtil.delete("user:status:" + id);
        }
    }

    @Transactional
    public User findByUsername(String username) {
        LambdaQueryWrapper<User> queryWrapper = Wrappers.lambdaQuery();
        if (username != null && !username.isEmpty()) {
            queryWrapper.eq(User::getName, username); // 用户名模糊匹配
        }
        return userMapper.selectOne(queryWrapper);
    }

    public List<User> listAllUserByUsername(String username) {
        LambdaQueryWrapper<User> queryWrapper = Wrappers.lambdaQuery();
        if (username != null && !username.isEmpty()) {
            queryWrapper.like(User::getName, username); // 用户名模糊匹配
        }
        return userMapper.selectList(queryWrapper);
    }

    @Override
    public Map<String, Object> getAllUsers(String username) {
        Map<String, Object> result = new HashMap<>();

        // 查询所有符合条件的用户
        LambdaQueryWrapper<User> queryWrapper = Wrappers.lambdaQuery();
        queryWrapper.ne(User::getRole, "ai"); // 排除 role 为 ai 的用户
        if (username != null && !username.isEmpty()) {
            queryWrapper.like(User::getName, username);
        }
        List<User> users = this.list(queryWrapper);

        if (users.isEmpty()) {
            result.put("total", 0L);
            result.put("list", Collections.emptyList());
            return result;
        }

        // 转换为 UserVO（不包含登录状态和设备数）
        List<UserVO> voList = users.stream().map(user -> {
            UserVO vo = new UserVO();
            BeanUtil.copyProperties(user, vo);
            return vo;
        }).toList();

        result.put("total", (long) users.size());
        result.put("list", voList);
        return result;
    }

    @Override
    public void saveUserAndStatus(User user) {
        this.save(user);
        redisUtil.set("user:status:" + user.getId(), "0");
    }
}

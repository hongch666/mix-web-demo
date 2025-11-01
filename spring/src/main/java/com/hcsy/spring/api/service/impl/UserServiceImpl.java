package com.hcsy.spring.api.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.toolkit.Wrappers;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;

import lombok.RequiredArgsConstructor;

import com.hcsy.spring.api.mapper.UserMapper;
import com.hcsy.spring.api.service.UserService;
import com.hcsy.spring.common.utils.RedisUtil;
import com.hcsy.spring.entity.po.User;

import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@RequiredArgsConstructor
@Transactional
public class UserServiceImpl extends ServiceImpl<UserMapper, User> implements UserService {
    private final UserMapper userMapper;
    private final RedisUtil redisUtil;

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

        // 4. 设置每个用户的登录状态（从 Redis 映射中获取）
        for (User user : users) {
            user.setLoginStatus(loginStatusMap.getOrDefault(user.getId(), 0));
        }

        // 5. 获取总数
        long total = userMapper.countUsersByUsername(username);

        // 6. 返回结果
        result.put("total", total);
        result.put("list", users);
        return result;
    }

    @Transactional
    public void saveUserAndStatus(User user) {
        userMapper.insert(user);
        redisUtil.set("user:status:" + user.getId(), "0");
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

}

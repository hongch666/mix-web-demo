package com.hcsy.spring.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.core.toolkit.Wrappers;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.hcsy.spring.po.Article;
import com.hcsy.spring.po.User;
import com.hcsy.spring.service.UserService;
import com.hcsy.spring.utils.RedisUtil;

import lombok.RequiredArgsConstructor;

import com.hcsy.spring.dto.UserQueryDTO;
import com.hcsy.spring.mapper.UserMapper;
import com.hcsy.spring.po.User;

import java.util.HashMap;
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
    public IPage<User> listUsersWithFilter(Page<User> page, String username) {
        LambdaQueryWrapper<User> queryWrapper = Wrappers.lambdaQuery();
        if (username != null && !username.isEmpty()) {
            queryWrapper.like(User::getName, username); // 用户名模糊匹配
        }
        return this.page(page, queryWrapper);
    }

    public void saveUserAndStatus(User user) {
        userMapper.insert(user);
        redisUtil.set("user:status:" + user.getId(), "0");
    }

}

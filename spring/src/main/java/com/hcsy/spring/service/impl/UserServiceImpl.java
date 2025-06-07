package com.hcsy.spring.service.impl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.hcsy.spring.po.User;
import com.hcsy.spring.service.UserService;
import com.hcsy.spring.utils.RedisUtil;

import lombok.RequiredArgsConstructor;

import com.hcsy.spring.mapper.UserMapper;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@RequiredArgsConstructor
@Transactional
public class UserServiceImpl extends ServiceImpl<UserMapper, User> implements UserService {
    private final UserMapper userMapper;
    private final RedisUtil redisUtil;

    public void saveUserAndStatus(User user) {
        userMapper.insert(user);
        redisUtil.set("user:status:" + user.getId(), "0");
    }
}

package com.hcsy.spring.service.impl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.hcsy.spring.po.User;
import com.hcsy.spring.service.UserService;
import com.hcsy.spring.mapper.UserMapper;
import org.springframework.stereotype.Service;

@Service
public class UserServiceImpl extends ServiceImpl<UserMapper, User> implements UserService {
    // 可扩展自定义方法实现
}

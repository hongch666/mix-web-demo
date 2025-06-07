package com.hcsy.spring.service;

import com.hcsy.spring.po.User;

import com.baomidou.mybatisplus.extension.service.IService;

public interface UserService extends IService<User> {
    void saveUserAndStatus(User user);
}

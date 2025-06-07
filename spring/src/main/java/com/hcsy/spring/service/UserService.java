package com.hcsy.spring.service;

import com.hcsy.spring.dto.UserQueryDTO;
import com.hcsy.spring.po.Article;
import com.hcsy.spring.po.User;

import java.util.Map;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.baomidou.mybatisplus.extension.service.IService;

public interface UserService extends IService<User> {
    IPage<User> listUsersWithFilter(Page<User> page, String username);

    void saveUserAndStatus(User user);

}

package com.hcsy.spring.api.service;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.baomidou.mybatisplus.extension.service.IService;
import com.hcsy.spring.entity.po.User;

import java.util.List;

public interface UserService extends IService<User> {
    IPage<User> listUsersWithFilter(Page<User> page, String username);

    void saveUserAndStatus(User user);

    void deleteUserAndStatusById(Long id);

    void deleteUsersAndStatusByIds(List<Long> ids);

    User findByUsername(String username);

}

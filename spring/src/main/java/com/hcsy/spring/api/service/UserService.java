package com.hcsy.spring.api.service;

import com.baomidou.mybatisplus.extension.service.IService;
import com.hcsy.spring.entity.po.User;

import java.util.List;
import java.util.Map;

public interface UserService extends IService<User> {
    Map<String, Object> listUsersWithFilter(long page, long size, String username);

    void saveUserAndStatus(User user);

    void deleteUserAndStatusById(Long id);

    void deleteUsersAndStatusByIds(List<Long> ids);

    User findByUsername(String username);

    List<User> listAllUserByUsername(String username);

}

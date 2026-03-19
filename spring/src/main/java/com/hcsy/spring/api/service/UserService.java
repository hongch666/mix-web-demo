package com.hcsy.spring.api.service;

import java.util.List;

import com.baomidou.mybatisplus.extension.service.IService;
import com.hcsy.spring.entity.po.User;
import com.hcsy.spring.entity.vo.UserListVO;

public interface UserService extends IService<User> {
    UserListVO listUsersWithFilter(long page, long size, String username);

    UserListVO getAllUsers(String username);

    void saveUserAndStatus(User user);

    void deleteUserAndStatusById(Long id);

    void deleteUsersAndStatusByIds(List<Long> ids);

    User findByUsername(String username);

    User findByEmail(String email);

    List<User> listAllUserByUsername(String username);

}

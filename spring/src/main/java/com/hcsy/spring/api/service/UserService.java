package com.hcsy.spring.api.service;

import java.util.List;

import com.baomidou.mybatisplus.extension.service.IService;
import com.hcsy.spring.entity.dto.EmailLoginDTO;
import com.hcsy.spring.entity.dto.LoginDTO;
import com.hcsy.spring.entity.dto.UserRegisterDTO;
import com.hcsy.spring.entity.po.User;
import com.hcsy.spring.entity.vo.UserListVO;
import com.hcsy.spring.entity.vo.UserLoginVO;

public interface UserService extends IService<User> {
    UserListVO listUsersWithFilter(long page, long size, String username);

    UserListVO getAllUsers(String username);

    void saveUserAndStatus(User user);

    void deleteUserAndStatusById(Long id);

    void deleteUsersAndStatusByIds(List<Long> ids);

    User findByUsername(String username);

    User findByEmail(String email);

    List<User> listAllUserByUsername(String username);

    UserLoginVO login(LoginDTO loginDTO);

    UserLoginVO emailLogin(EmailLoginDTO emailLoginDTO);

    void registerUser(UserRegisterDTO registerDTO);

}

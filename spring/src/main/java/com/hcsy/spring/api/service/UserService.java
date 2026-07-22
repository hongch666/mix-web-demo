package com.hcsy.spring.api.service;

import java.util.Collection;
import java.util.List;

import com.hcsy.spring.entity.dto.EmailLoginDTO;
import com.hcsy.spring.entity.dto.GithubTokenExchangeDTO;
import com.hcsy.spring.entity.dto.GithubTokenTicketCreateDTO;
import com.hcsy.spring.entity.dto.LoginDTO;
import com.hcsy.spring.entity.dto.ResetPasswordDTO;
import com.hcsy.spring.entity.dto.UserCreateDTO;
import com.hcsy.spring.entity.dto.UserRegisterDTO;
import com.hcsy.spring.entity.dto.UserUpdateDTO;
import com.hcsy.spring.entity.po.User;
import com.hcsy.spring.entity.vo.GithubTokenTicketVO;
import com.hcsy.spring.entity.vo.UserListVO;
import com.hcsy.spring.entity.vo.UserLoginVO;

import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

public interface UserService {
    Mono<UserListVO> listUsersWithFilter(long page, long size, String username);

    Mono<UserListVO> getAllUsers(String username);

    Mono<UserListVO> getAllAiUsers();

    Mono<User> saveUserAndStatus(User user);

    Mono<Void> deleteUserAndStatusById(Long id);

    Mono<Void> deleteUsersAndStatusByIds(List<Long> ids);

    Mono<User> findByUsername(String username);

    Mono<User> findByEmail(String email);

    Flux<User> listAllUserByUsername(String username);

    Mono<UserLoginVO> login(LoginDTO loginDTO);

    Mono<UserLoginVO> emailLogin(EmailLoginDTO emailLoginDTO);

    Mono<GithubTokenTicketVO> createGithubTokenTicket(GithubTokenTicketCreateDTO dto);

    Mono<UserLoginVO> exchangeGithubTokenTicket(GithubTokenExchangeDTO dto);

    Mono<Void> registerUser(UserRegisterDTO registerDTO);

    Mono<Void> createUser(UserCreateDTO userDto);

    Mono<Void> updateUserInfo(UserUpdateDTO userDto);

    Mono<Void> resetPassword(ResetPasswordDTO resetPasswordDTO);

    Mono<Void> resetAllPasswords();

    Mono<Void> resetUserPassword(Long userId);

    Mono<Integer> getUserLoginStatus(Long userId);

    Mono<Void> updateUserStatus(Long userId, String status);

    Flux<Long> getNormalUserIds();

    Flux<Long> getAiUserIds();

    Mono<Long> countNormalUsers();

    Mono<Long> countAiUsers();

    Mono<User> getById(Long id);

    Flux<User> listByIds(Collection<Long> ids);
}

package com.hcsy.spring.api.service;

import java.util.List;

import com.baomidou.mybatisplus.extension.service.IService;
import com.hcsy.spring.entity.dto.EmailLoginDTO;
import com.hcsy.spring.entity.dto.GithubTokenExchangeDTO;
import com.hcsy.spring.entity.dto.GithubTokenTicketCreateDTO;
import com.hcsy.spring.entity.dto.LoginDTO;
import com.hcsy.spring.entity.dto.UserRegisterDTO;
import com.hcsy.spring.entity.po.User;
import com.hcsy.spring.entity.vo.GithubTokenTicketVO;
import com.hcsy.spring.entity.vo.UserListVO;
import com.hcsy.spring.entity.vo.UserLoginVO;

public interface UserService extends IService<User> {
    UserListVO listUsersWithFilter(long page, long size, String username);

    UserListVO getAllUsers(String username);

    UserListVO getAllAiUsers();

    void saveUserAndStatus(User user);

    void deleteUserAndStatusById(Long id);

    void deleteUsersAndStatusByIds(List<Long> ids);

    User findByUsername(String username);

    User findByEmail(String email);

    List<User> listAllUserByUsername(String username);

    UserLoginVO login(LoginDTO loginDTO);

    UserLoginVO emailLogin(EmailLoginDTO emailLoginDTO);

    GithubTokenTicketVO createGithubTokenTicket(GithubTokenTicketCreateDTO dto);

    UserLoginVO exchangeGithubTokenTicket(GithubTokenExchangeDTO dto);

    void registerUser(UserRegisterDTO registerDTO);

    /**
     * 获取用户登录状态（从Redis）
     *
     * @param userId 用户ID
     * @return 1-在线，0-离线
     */
    int getUserLoginStatus(Long userId);

    /**
     * 更新用户登录状态（写入Redis）
     *
     * @param userId 用户ID
     * @param status 1-在线，0-离线
     */
    void updateUserStatus(Long userId, String status);

    /**
     * 查询所有非 AI 用户的 ID 列表
     * 通过 SQL 直接返回 ID，避免内存中 stream 操作
     *
     * @return 非 AI 用户的 ID 列表
     */
    List<Long> getNormalUserIds();

    /**
     * 查询所有 AI 用户的 ID 列表
     * 通过 SQL 直接返回 ID，避免内存中 stream 操作
     *
     * @return AI 用户的 ID 列表
     */
    List<Long> getAiUserIds();

    /**
     * 统计非 AI 用户总数
     * 通过 SQL COUNT 统计，避免内存中 list.size() 操作
     *
     * @return 非 AI 用户总数
     */
    long countNormalUsers();

    /**
     * 统计 AI 用户总数
     * 通过 SQL COUNT 统计，避免内存中 list.size() 操作
     *
     * @return AI 用户总数
     */
    long countAiUsers();

}

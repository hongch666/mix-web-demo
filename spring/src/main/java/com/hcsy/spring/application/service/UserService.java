package com.hcsy.spring.application.service;

import java.util.Collection;
import java.util.List;

import com.hcsy.spring.entity.dto.EmailLoginDTO;
import com.hcsy.spring.entity.dto.GithubTokenExchangeDTO;
import com.hcsy.spring.entity.dto.GithubTokenTicketCreateDTO;
import com.hcsy.spring.entity.dto.GithubUserInternalDTO;
import com.hcsy.spring.entity.dto.LoginDTO;
import com.hcsy.spring.entity.dto.ResetPasswordDTO;
import com.hcsy.spring.entity.dto.UserCreateDTO;
import com.hcsy.spring.entity.dto.UserRegisterDTO;
import com.hcsy.spring.entity.dto.UserUpdateDTO;
import com.hcsy.spring.entity.po.User;
import com.hcsy.spring.entity.vo.GithubTokenTicketVO;
import com.hcsy.spring.entity.vo.KickOtherDevicesVO;
import com.hcsy.spring.entity.vo.UserListVO;
import com.hcsy.spring.entity.vo.UserLoginVO;
import com.hcsy.spring.entity.vo.UserSyncVO;
import com.hcsy.spring.entity.vo.UserVO;

import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

/**
 * 用户业务接口，定义用户注册登录（含邮箱与GitHub登录）、资料增删改查、密码重置、多设备管理与用户统计等响应式操作
 */
public interface UserService {
    /**
     * 邮件验证码发送结果枚举，标识已发送、邮箱非法、类型非法、注册邮箱已存在及邮箱不存在五种状态
     */
    enum EmailCodeSendOutcome {
        SENT, INVALID_EMAIL, INVALID_TYPE, EMAIL_EXISTS, EMAIL_NOT_FOUND
    }

    /**
     * 查询用户详情并附带登录状态与在线设备数
     */
    Mono<UserVO> getUserDetail(Long id);

    /**
     * 踢出用户除当前令牌外的其他设备会话，返回移除数与剩余在线设备数
     */
    Mono<KickOtherDevicesVO> kickOtherDevices(Long userId, String accessToken);

    /**
     * 强制指定用户下线，用户不存在时返回false
     */
    Mono<Boolean> forceLogoutUser(Long userId);

    /**
     * 按用途类型校验邮箱后发送验证码，返回发送结果的Mono响应式结果
     */
    Mono<EmailCodeSendOutcome> sendVerificationCode(String email, String type);
    /**
     * 分页查询非AI用户列表，支持按用户名过滤并附带登录状态与在线设备数
     */
    Mono<UserListVO> listUsersWithFilter(long page, long size, String username);

    /**
     * 查询全部非AI用户列表，支持按用户名过滤，无过滤条件时走多级缓存
     */
    Mono<UserListVO> getAllUsers(String username);

    /**
     * 查询全部AI角色用户列表
     */
    Mono<UserListVO> getAllAiUsers();

    /**
     * 事务保存用户并初始化登录状态，未加密的密码自动加密后写入
     */
    Mono<User> saveUserAndStatus(User user);

    /**
     * 事务删除指定用户并清理其登录状态与角色缓存
     */
    Mono<Void> deleteUserAndStatusById(Long id);

    /**
     * 事务批量删除用户并清理其登录状态与角色缓存，存在缺失用户时抛出异常
     */
    Mono<Void> deleteUsersAndStatusByIds(List<Long> ids);

    /**
     * 根据用户名精确查询用户并返回Mono响应式结果
     */
    Mono<User> findByUsername(String username);

    /**
     * 根据邮箱精确查询用户并返回Mono响应式结果
     */
    Mono<User> findByEmail(String email);

    /**
     * 按用户名模糊查询用户，未提供名称时返回全部用户的Flux流
     */
    Flux<User> listAllUserByUsername(String username);

    /**
     * 按GitHub ID查找用户，存在则更新GitHub资料，不存在则使用默认密码创建新用户
     */
    Mono<User> findOrCreateGithubUser(GithubUserInternalDTO dto);

    /**
     * 判断指定用户是否为管理员角色
     */
    Mono<Boolean> isAdminUser(Long userId);

    /**
     * 校验图形验证码与密码后为用户创建登录会话
     */
    Mono<UserLoginVO> login(LoginDTO loginDTO);

    /**
     * 校验图形验证码与邮箱验证码后按邮箱登录并创建会话
     */
    Mono<UserLoginVO> emailLogin(EmailLoginDTO emailLoginDTO);

    /**
     * 为用户创建登录会话并将登录凭证以一次性票据形式缓存于Redis，返回票据信息
     */
    Mono<GithubTokenTicketVO> createGithubTokenTicket(GithubTokenTicketCreateDTO dto);

    /**
     * 一次性兑换GitHub登录票据并删除缓存，返回对应的登录凭证
     */
    Mono<UserLoginVO> exchangeGithubTokenTicket(GithubTokenExchangeDTO dto);

    /**
     * 校验邮箱未被注册及验证码有效后创建本地注册用户，成功后标记邮箱已验证
     */
    Mono<User> registerUser(UserRegisterDTO registerDTO);

    /**
     * 管理端创建用户，密码缺省时使用配置的默认密码并加密保存
     */
    Mono<User> createUser(UserCreateDTO userDto);

    /**
     * 更新用户资料，保留GitHub信息与注册时间等受保护字段，填写密码时重新加密
     */
    Mono<Void> updateUserInfo(UserUpdateDTO userDto);

    /**
     * 校验邮箱验证码后将指定邮箱用户的密码重置为新密码
     */
    Mono<Void> resetPassword(ResetPasswordDTO resetPasswordDTO);

    /**
     * 将全库用户密码批量重置为配置的默认重置密码
     */
    Mono<Void> resetAllPasswords();

    /**
     * 将指定用户的密码重置为配置的默认重置密码
     */
    Mono<Void> resetUserPassword(Long userId);

    /**
     * 查询用户登录状态，返回1在线0离线的Mono结果
     */
    Mono<Integer> getUserLoginStatus(Long userId);

    /**
     * 更新用户登录状态并失效用户列表缓存
     */
    Mono<Void> updateUserStatus(Long userId, String status);

    /**
     * 查询全部非AI用户的ID的Flux流
     */
    Flux<Long> getNormalUserIds();

    /**
     * 查询全部AI角色用户的ID的Flux流
     */
    Flux<Long> getAiUserIds();

    /**
     * 统计非AI用户数量并返回Mono响应式结果
     */
    Mono<Long> countNormalUsers();

    /**
     * 统计AI角色用户数量并返回Mono响应式结果
     */
    Mono<Long> countAiUsers();

    /**
     * 根据ID查询用户并返回Mono响应式结果
     */
    Mono<User> getById(Long id);

    /**
     * 根据ID集合批量查询用户并返回Flux响应式流
     */
    Flux<User> listByIds(Collection<Long> ids);

    /**
     * 获取用户数据，用于Neo4j同步
     *
     * @param updatedAfter
     *                         增量同步时间（ISO格式），为空则全量
     */
    Mono<List<UserSyncVO>> getNeo4jSyncUsers(String updatedAfter);
}

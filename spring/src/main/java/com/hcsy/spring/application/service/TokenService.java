package com.hcsy.spring.application.service;

import java.util.List;

import com.hcsy.spring.entity.dto.AuthIdentityDTO;
import com.hcsy.spring.entity.vo.TokenRefreshVO;
import com.hcsy.spring.entity.vo.UserLoginVO;

import reactor.core.publisher.Mono;

/**
 * 登录令牌业务接口，定义访问令牌校验、登录会话创建、刷新令牌轮换、多设备会话管理与过期Token清理等响应式操作
 */
public interface TokenService {
    /**
     * 校验访问令牌并返回用户身份信息的Mono响应式结果
     */
    Mono<AuthIdentityDTO> validateAccessToken(String accessToken);

    /**
     * 校验网关转发的访问令牌，支持从 Authorization 头、令牌参数或转发 URI 中提取，返回用户身份
     */
    Mono<AuthIdentityDTO> validateGatewayAccessToken(
        String authorization, String accessToken, String forwardedUri);

    /**
     * 为用户创建登录会话，生成访问与刷新令牌并写入Redis后返回登录信息
     */
    Mono<UserLoginVO> createLoginSession(Long userId, String username);

    /**
     * 使用刷新令牌轮换新令牌对，基于分布式锁防止并发刷新，返回Mono响应式结果
     */
    Mono<TokenRefreshVO> refreshToken(String refreshToken);

    /**
     * 根据访问令牌删除对应的登录会话
     */
    Mono<Void> removeSessionByAccessToken(String accessToken);

    /**
     * 删除指定用户的指定会话，清理令牌索引并在无剩余会话时更新登录状态
     */
    Mono<Void> removeSession(Long userId, String sessionId);

    /**
     * 校验访问令牌在Redis中的反向索引与会话记录是否匹配，返回Boolean的Mono结果
     */
    Mono<Boolean> validateAccessTokenInRedis(Long userId, String sessionId, String accessToken);

    /**
     * 统计用户在线设备数量，返回Mono包装的会话集合大小
     */
    Mono<Long> getUserOnlineDeviceCount(Long userId);

    /**
     * 查询用户全部会话ID列表，返回Mono响应式结果
     */
    Mono<List<String>> getUserSessions(Long userId);

    /**
     * 强制指定用户下线，删除其全部会话并将登录状态置为离线
     */
    Mono<Void> forceLogoutUser(Long userId);

    /**
     * 踢出除当前令牌外的其他设备会话，返回被移除的会话数量
     */
    Mono<Integer> removeOtherSessions(Long userId, String currentAccessToken);

    /**
     * 清理全部用户的过期会话，返回Mono空信号的异步任务
     */
    Mono<Void> cleanupExpiredTokens();
}

package com.hcsy.spring.application.service;

import java.util.List;

import com.hcsy.spring.common.constants.BusinessType;

import reactor.core.publisher.Mono;

/**
 * 权限校验组件
 * 承载角色读取与资源归属判定，切面只负责从切点取参数并编排调用
 */
public interface PermissionChecker {

    /**
     * 判断用户是否具备任一指定角色
     */
    Mono<Boolean> hasAnyRole(Long userId, String[] roles);

    /**
     * 判断目标资源是否属于指定用户，目标标识为空时返回 false
     */
    Mono<Boolean> isOwner(Long currentUserId, Long targetId, BusinessType businessType);

    /**
     * 解析批量资源的唯一所有者，资源不存在或归属不一致时返回业务异常
     */
    Mono<Long> resolveSharedOwner(List<Long> resourceIds, BusinessType businessType);

    /**
     * 按用户名解析用户 ID
     */
    Mono<Long> resolveUserIdByUsername(String username);
}

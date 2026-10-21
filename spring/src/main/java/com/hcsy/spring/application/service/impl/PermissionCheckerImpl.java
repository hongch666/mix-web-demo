package com.hcsy.spring.application.service.impl;

import java.util.Arrays;
import java.util.List;

import org.springframework.stereotype.Service;

import com.hcsy.spring.application.service.ArticleService;
import com.hcsy.spring.application.service.CommentsService;
import com.hcsy.spring.application.service.PermissionChecker;
import com.hcsy.spring.application.service.UserService;
import com.hcsy.spring.common.constants.BusinessType;
import com.hcsy.spring.common.constants.HttpCode;
import com.hcsy.spring.common.constants.Messages;
import com.hcsy.spring.common.constants.RedisKeys;
import com.hcsy.spring.common.exceptions.BusinessException;
import com.hcsy.spring.common.utils.CacheUtil;
import com.hcsy.spring.entity.po.Article;
import com.hcsy.spring.entity.po.Comments;
import com.hcsy.spring.entity.po.User;

import lombok.RequiredArgsConstructor;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

/**
 * 权限校验实现
 * 角色读取走多级缓存，资源归属按业务类型分发到对应服务
 */
@Service
@RequiredArgsConstructor
public class PermissionCheckerImpl implements PermissionChecker {

    /** 用户角色多级缓存，TTL 走全局默认，用户修改与删除时按同一份定义失效 */
    static final CacheUtil.CacheOptions<String> USER_ROLE_CACHE = CacheUtil.CacheOptions.fixed(
        RedisKeys.userRoleCacheName(), RedisKeys.userCacheInvalidationChannel(), 1000);

    private final UserService userService;
    private final ArticleService articleService;
    private final CommentsService commentsService;
    private final CacheUtil cacheUtil;

    @Override
    public Mono<Boolean> hasAnyRole(Long userId, String[] roles) {
        if (userId == null || roles == null || roles.length == 0) {
            return Mono.just(false);
        }
        List<String> allowedRoles = Arrays.asList(roles);
        return getRole(userId)
            .map(allowedRoles::contains)
            .defaultIfEmpty(false);
    }

    /**
     * 实现判断当前用户是否为指定用户、文章或评论的属主
     */
    @Override
    public Mono<Boolean> isOwner(Long currentUserId, Long targetId, BusinessType businessType) {
        if (currentUserId == null || targetId == null || businessType == null) {
            return Mono.just(false);
        }
        return switch (businessType) {
            case USER -> Mono.just(currentUserId.equals(targetId));
            case ARTICLE -> articleService.getById(targetId)
                .map(article -> currentUserId.equals(article.getUserId()))
                .defaultIfEmpty(false);
            case COMMENT -> commentsService.getById(targetId)
                .map(comment -> currentUserId.equals(comment.getUserId()))
                .defaultIfEmpty(false);
            case CATEGORY, SUB_CATEGORY, CATEGORY_REFERENCE -> Mono.just(false);
        };
    }

    /**
     * 实现解析一批资源的共同属主，归属不一致或缺失时抛业务异常
     */
    @Override
    public Mono<Long> resolveSharedOwner(List<Long> resourceIds, BusinessType businessType) {
        if (resourceIds == null || resourceIds.isEmpty() || businessType == null) {
            return Mono.empty();
        }
        Flux<Long> owners = switch (businessType) {
            case ARTICLE -> articleService.listByIds(resourceIds)
                .switchIfEmpty(Mono.error(notFound(Messages.UNDEFINED_ARTICLES)))
                .map(Article::getUserId);
            case COMMENT -> Flux.fromIterable(resourceIds)
                .concatMap(id -> commentsService.getById(id)
                    .switchIfEmpty(Mono.error(notFound(Messages.COMMENT_ID + id))))
                .map(Comments::getUserId);
            case USER -> Flux.fromIterable(resourceIds);
            case CATEGORY, SUB_CATEGORY, CATEGORY_REFERENCE -> Flux.empty();
        };
        return owners.collectList().flatMap(ownerIds -> {
            if (ownerIds.size() != resourceIds.size() || ownerIds.stream().anyMatch(id -> id == null)) {
                return Mono.error(notFound(Messages.NO_SOURCE));
            }
            Long owner = ownerIds.get(0);
            if (ownerIds.stream().anyMatch(id -> !owner.equals(id))) {
                return Mono.error(BusinessException.builder().httpStatus(HttpCode.BAD_REQUEST)
                    .errorMessage(Messages.MULTIPLE_RESOURCE_OWNERS).build());
            }
            return Mono.just(owner);
        });
    }

    /**
     * 实现按用户名解析用户ID
     */
    @Override
    public Mono<Long> resolveUserIdByUsername(String username) {
        return userService.findByUsername(username).map(User::getId);
    }

    /**
     * 读取用户角色，缓存未命中时回源数据库
     * 用户不存在时缓存空字符串，避免每次请求都穿透到数据库
     */
    private Mono<String> getRole(Long userId) {
        return cacheUtil.get(USER_ROLE_CACHE, userId, RedisKeys.userRole(userId), String.class,
            () -> userService.getById(userId).map(User::getRole).defaultIfEmpty(""));
    }

    /**
     * 构造404资源不存在的业务异常
     */
    private BusinessException notFound(String message) {
        return BusinessException.builder().httpStatus(HttpCode.NOT_FOUND).errorMessage(message).build();
    }
}

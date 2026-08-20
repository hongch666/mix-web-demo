package com.hcsy.spring.api.controller;

import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import com.hcsy.spring.api.service.UserService;
import com.hcsy.spring.common.constants.HttpCode;
import com.hcsy.spring.common.constants.Messages;
import com.hcsy.spring.common.utils.Result;
import com.hcsy.spring.core.annotation.ApiLog;
import com.hcsy.spring.core.annotation.RequireInternalToken;
import com.hcsy.spring.entity.dto.BatchIdsDTO;
import com.hcsy.spring.entity.dto.GithubUserInternalDTO;
import com.hcsy.spring.entity.vo.UserVO;

import cn.hutool.core.bean.BeanUtil;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import reactor.core.publisher.Mono;

/**
 * 用户模块内部接口（供 NestJS 服务远程调用）
 */
@RestController
@RequestMapping("/users/internal")
@RequiredArgsConstructor
@Tag(name = "用户内部接口", description = "供 NestJS 服务远程调用的用户内部接口")
public class UserInternalController {

    private final UserService userService;

    @GetMapping("/{id}")
    @Operation(summary = "根据ID查询用户（内部）", description = "根据ID查询用户，供 NestJS 服务远程调用")
    @RequireInternalToken
    @ApiLog("内部查询用户")
    public Mono<Result<UserVO>> getUserById(@PathVariable Long id) {
        return userService.getById(id)
            .map(user -> {
                UserVO vo = BeanUtil.copyProperties(user, UserVO.class);
                return Result.success(vo);
            })
            .defaultIfEmpty(Result.<UserVO>error(HttpCode.NOT_FOUND, Messages.UNDEFINED_USER));
    }

    @PostMapping("/batch")
    @Operation(summary = "批量查询用户（内部）", description = "根据ID列表批量查询用户，供 NestJS 服务远程调用")
    @RequireInternalToken
    @ApiLog("内部批量查询用户")
    public Mono<Result<List<UserVO>>> getUserByIds(@Valid @RequestBody BatchIdsDTO dto) {
        return userService.listByIds(dto.getIds())
            .collectList()
            .map(users -> users.stream()
                .map(user -> BeanUtil.copyProperties(user, UserVO.class))
                .collect(Collectors.toList()))
            .map(Result::success);
    }

    @GetMapping("/by-name")
    @Operation(summary = "根据用户名模糊搜索用户（内部）", description = "根据用户名或GitHub登录名模糊搜索，供 NestJS 服务远程调用")
    @RequireInternalToken
    @ApiLog("内部搜索用户")
    public Mono<Result<List<UserVO>>> getUsersByName(@RequestParam String name) {
        return userService.listAllUserByUsername(name)
            .collectList()
            .map(users -> users.stream()
                .map(user -> BeanUtil.copyProperties(user, UserVO.class))
                .collect(Collectors.toList()))
            .map(Result::success);
    }

    @GetMapping("/by-github-id/{githubId}")
    @Operation(summary = "根据GitHub ID查询用户（内部）", description = "根据GitHub ID查询用户，供 NestJS 服务远程调用")
    @RequireInternalToken
    @ApiLog("内部GitHub ID查询用户")
    public Mono<Result<UserVO>> getUserByGithubId(@PathVariable Long githubId) {
        return userService.findByGithubId(githubId)
            .map(user -> {
                UserVO vo = BeanUtil.copyProperties(user, UserVO.class);
                return Result.success(vo);
            })
            .defaultIfEmpty(Result.<UserVO>error(HttpCode.NOT_FOUND, Messages.UNDEFINED_USER));
    }

    @PostMapping("/github-user")
    @Operation(summary = "创建或更新GitHub用户（内部）", description = "GitHub OAuth登录后创建或更新用户，供 NestJS 服务远程调用")
    @RequireInternalToken
    @ApiLog("内部创建或更新GitHub用户")
    public Mono<Result<UserVO>> findOrCreateGithubUser(@Valid @RequestBody GithubUserInternalDTO dto) {
        return userService.findOrCreateGithubUser(dto)
            .map(user -> {
                UserVO vo = BeanUtil.copyProperties(user, UserVO.class);
                return Result.success(vo);
            });
    }

    @GetMapping("/{id}/is-admin")
    @Operation(summary = "判断用户是否为管理员（内部）", description = "根据用户ID判断是否为管理员，供 NestJS 服务远程调用")
    @RequireInternalToken
    @ApiLog("内部判断管理员")
    public Mono<Result<Boolean>> isAdminUser(@PathVariable Long id) {
        return userService.isAdminUser(id)
            .map(Result::success);
    }

    @GetMapping("/neo4j-sync")
    @Operation(summary = "获取用户表数据用于Neo4j同步（内部）", description = "获取用户表数据，支持增量同步，供FastAPI同步Neo4j使用")
    @RequireInternalToken
    @ApiLog("内部获取Neo4j同步用户数据")
    public Mono<Result<List<Map<String, Object>>>> getNeo4jSyncUsers(
        @RequestParam(required = false) String updatedAfter) {
        return userService.getNeo4jSyncUsers(updatedAfter).map(Result::success);
    }
}

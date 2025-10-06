package com.hcsy.spring.api.controller;

import com.hcsy.spring.api.service.UserService;
import com.hcsy.spring.common.annotation.ApiLog;
import com.hcsy.spring.common.annotation.RequirePermission;
import com.hcsy.spring.common.utils.JwtUtil;
import com.hcsy.spring.common.utils.RedisUtil;
import com.hcsy.spring.common.utils.SimpleLogger;
import com.hcsy.spring.entity.dto.LoginDTO;
import com.hcsy.spring.entity.dto.UserCreateDTO;
import com.hcsy.spring.entity.dto.UserQueryDTO;
import com.hcsy.spring.entity.dto.UserUpdateDTO;
import com.hcsy.spring.entity.po.Result;
import com.hcsy.spring.entity.po.User;

import cn.hutool.core.bean.BeanUtil;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;

import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.springframework.web.bind.annotation.*;
import org.springframework.cache.annotation.CacheConfig;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.cache.annotation.CacheEvict;
import org.springframework.cache.annotation.Caching;

@RestController
@RequestMapping("/users")
@RequiredArgsConstructor
@CacheConfig(cacheNames = "user")
@Tag(name = "用户模块", description = "用户相关接口")
public class UserController {
    private final UserService userService;
    private final RedisUtil redisUtil;
    private final JwtUtil jwtUtil;
    private final SimpleLogger logger;

    @GetMapping()
    @Operation(summary = "获取用户信息", description = "分页获取用户信息列表，并支持用户名模糊查询")
    @Cacheable(value = "userPage", key = "#queryDTO.page + '-' + #queryDTO.size + '-' + (#queryDTO.username == null ? '' : #queryDTO.username)")
    @ApiLog("获取用户信息")
    public Result listUsers(@ModelAttribute UserQueryDTO queryDTO) {
        Map<String, Object> data = userService.listUsersWithFilter(
                queryDTO.getPage(),
                queryDTO.getSize(),
                queryDTO.getUsername());
        return Result.success(data);
    }

    @PostMapping
    @Operation(summary = "新增用户", description = "通过请求体创建用户信息")
    @RequirePermission(roles = { "admin" })
    @Caching(evict = {
            @CacheEvict(value = "userPage", allEntries = true)
    })
    @ApiLog("新增用户")
    public Result addUser(@Valid @RequestBody UserCreateDTO userDto) {
        User user = BeanUtil.copyProperties(userDto, User.class);
        user.setRole("user");
        userService.saveUserAndStatus(user);
        return Result.success();
    }

    @DeleteMapping("/{id}")
    @Operation(summary = "删除用户", description = "根据id删除用户")
    @RequirePermission(roles = { "admin" })
    @Caching(evict = {
            @CacheEvict(value = "userPage", allEntries = true),
            @CacheEvict(value = "userById", key = "#id")
    })
    @ApiLog("删除用户")
    public Result deleteUser(@PathVariable Long id) {
        userService.deleteUserAndStatusById(id);
        return Result.success();
    }

    @DeleteMapping("/batch/{ids}")
    @Operation(summary = "批量删除用户", description = "根据id数组批量删除用户，多个id用英文逗号分隔")
    @RequirePermission(roles = { "admin" })
    @Caching(evict = {
            @CacheEvict(value = "userPage", allEntries = true),
            @CacheEvict(value = "userById", allEntries = true)
    })
    @ApiLog("批量删除用户")
    public Result deleteUsers(@PathVariable String ids) {
        List<Long> idList = Arrays.stream(ids.split(","))
                .map(String::trim)
                .filter(s -> !s.isEmpty())
                .map(Long::valueOf)
                .toList();
        userService.deleteUsersAndStatusByIds(idList);
        return Result.success();
    }

    @GetMapping("/{id}")
    @Operation(summary = "查询用户", description = "根据id查询用户")
    @Cacheable(value = "userById", key = "#id")
    @ApiLog("查询用户")
    public Result getUserById(@PathVariable Long id) {
        User user = userService.getById(id);
        return Result.success(user);
    }

    @PutMapping
    @Operation(summary = "修改用户", description = "通过请求体修改用户信息")
    @RequirePermission(roles = { "admin" }, allowSelf = true, targetUserIdParam = "userDto")
    @Caching(evict = {
            @CacheEvict(value = "userPage", allEntries = true),
            @CacheEvict(value = "userById", key = "#userDto.id")
    })
    @ApiLog("修改用户")
    public Result updateUser(@Valid @RequestBody UserUpdateDTO userDto) {
        User user = BeanUtil.copyProperties(userDto, User.class);
        userService.updateById(user);
        return Result.success();
    }

    @PutMapping("/status/{id}")
    @Operation(summary = "修改用户状态", description = "根据用户ID修改用户状态（存储在Redis中）")
    @RequirePermission(roles = { "admin" }, allowSelf = true)
    @Caching(evict = {
            @CacheEvict(value = "userPage", allEntries = true),
            @CacheEvict(value = "userById", key = "#id")
    })
    @ApiLog("修改用户状态")
    public Result updateUserStatus(@PathVariable Long id, @RequestParam String status) {
        String key = "user:status:" + id;
        redisUtil.set(key, status); // 设置为永久保存
        return Result.success();
    }

    @GetMapping("/status/{id}")
    @Operation(summary = "查询用户状态", description = "根据用户ID查询用户状态（存储在Redis中）")
    @ApiLog("查询用户状态")
    public Result getUserStatus(@PathVariable Long id) {
        String key = "user:status:" + id;
        String status = redisUtil.get(key);
        return Result.success(status);
    }

    @PostMapping("/login")
    @Operation(summary = "用户登录", description = "根据用户名和密码进行登录，成功后返回JWT令牌")
    public Result login(@RequestBody LoginDTO loginDTO) {
        logger.info("POST /users/login: " + "用户登录\nLoginDTO: %s", loginDTO);
        User user = userService.findByUsername(loginDTO.getName());
        if (user == null || !user.getPassword().equals(loginDTO.getPassword())) {
            return Result.error("用户名或密码错误");
        }
        String key = "user:status:" + user.getId();
        redisUtil.set(key, "1");
        String token = jwtUtil.generateToken(user.getId(), user.getName());
        Map<String, Object> data = new HashMap<>();
        data.put("token", token);
        data.put("userId", user.getId());
        data.put("username", user.getName());
        return Result.success(data);
    }

    @PostMapping("/logout/{id}")
    @Operation(summary = "用户登出", description = "根据用户ID登出，清除Redis中的用户状态")
    @Caching(evict = {
            @CacheEvict(value = "userById", key = "#id"),
            @CacheEvict(value = "userPage", allEntries = true)
    })
    @ApiLog("用户登出")
    public Result logout(@PathVariable Long id) {
        String key = "user:status:" + id;
        redisUtil.set(key, "0");
        return Result.success();
    }

    @PostMapping("/register")
    @Operation(summary = "用户注册", description = "注册新用户")
    @Caching(evict = {
            @CacheEvict(value = "userPage", allEntries = true)
    })
    public Result registerUser(@Valid @RequestBody UserCreateDTO userDto) {
        logger.info("POST /users/register: " + "用户注册\nUserCreateDTO: %s", userDto);
        User user = BeanUtil.copyProperties(userDto, User.class);
        user.setRole("user");
        userService.saveUserAndStatus(user);
        return Result.success();
    }

}

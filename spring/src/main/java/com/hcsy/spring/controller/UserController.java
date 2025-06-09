package com.hcsy.spring.controller;

import com.hcsy.spring.dto.LoginDTO;
import com.hcsy.spring.dto.UserCreateDTO;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.hcsy.spring.dto.UserQueryDTO;
import com.hcsy.spring.dto.UserUpdateDTO;
import com.hcsy.spring.po.Result;
import com.hcsy.spring.po.User;
import com.hcsy.spring.service.UserService;
import com.hcsy.spring.utils.JwtUtil;
import com.hcsy.spring.utils.RedisUtil;

import cn.hutool.core.bean.BeanUtil;
import feign.Param;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;

import java.util.Collections;
import java.util.HashMap;
import java.util.Map;

import org.springframework.web.bind.annotation.*;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;

@RestController
@RequestMapping("/users")
@RequiredArgsConstructor
@Tag(name = "用户模块", description = "用户相关接口")
public class UserController {
    private final UserService userService;
    private final RedisUtil redisUtil;

    @GetMapping()
    @Operation(summary = "获取用户信息", description = "分页获取用户信息列表，并支持用户名模糊查询")
    public Result listUsers(@ModelAttribute UserQueryDTO queryDTO) {
        Page<User> userPage = new Page<>(queryDTO.getPage(), queryDTO.getSize());
        IPage<User> resultPage = userService.listUsersWithFilter(userPage, queryDTO.getUsername());
        Map<String, Object> data = new HashMap<>();
        data.put("total", resultPage.getTotal());
        data.put("list", resultPage.getRecords());
        return Result.success(data);
    }

    @PostMapping
    @Operation(summary = "新增用户", description = "通过请求体创建用户信息")
    public Result addUser(@Valid @RequestBody UserCreateDTO userDto) {
        User user = BeanUtil.copyProperties(userDto, User.class);
        userService.saveUserAndStatus(user);
        return Result.success();
    }

    @DeleteMapping("/{id}")
    @Operation(summary = "删除用户", description = "根据id删除用户")
    public Result deleteUser(@PathVariable Long id) {
        userService.deleteUserAndStatusById(id);
        return Result.success();
    }

    @GetMapping("/{id}")
    @Operation(summary = "查询用户", description = "根据id查询用户")
    public Result getUserById(@PathVariable Long id) {
        User user = userService.getById(id);
        return Result.success(user);
    }

    @PutMapping
    @Operation(summary = "修改用户", description = "通过请求体修改用户信息")
    public Result updateUser(@Valid @RequestBody UserUpdateDTO userDto) {
        User user = BeanUtil.copyProperties(userDto, User.class);
        userService.updateById(user);
        return Result.success();
    }

    @PutMapping("/status/{id}")
    @Operation(summary = "修改用户状态", description = "根据用户ID修改用户状态（存储在Redis中）")
    public Result updateUserStatus(@PathVariable Long id, @RequestParam String status) {
        String key = "user:status:" + id;
        redisUtil.set(key, status); // 设置为永久保存
        return Result.success();
    }

    @GetMapping("/status/{id}")
    @Operation(summary = "查询用户状态", description = "根据用户ID查询用户状态（存储在Redis中）")
    public Result getUserStatus(@PathVariable Long id) {
        String key = "user:status:" + id;
        String status = redisUtil.get(key);
        return Result.success(status);
    }

    @PostMapping("/login")
    public Result login(@RequestBody LoginDTO loginDTO) {
        User user = userService.findByUsername(loginDTO.getName());
        ;
        if (user == null || !user.getPassword().equals(loginDTO.getPassword())) {
            return Result.error("用户名或密码错误");
        }
        String key = "user:status:" + user.getId();
        redisUtil.set(key, "1"); // 设置为永久保存
        String token = JwtUtil.generateToken(user.getName());
        return Result.success(token);
    }

}

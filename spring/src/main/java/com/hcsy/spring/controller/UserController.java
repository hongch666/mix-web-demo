package com.hcsy.spring.controller;

import com.hcsy.spring.dto.UserCreateDTO;
import com.hcsy.spring.dto.UserUpdateDTO;
import com.hcsy.spring.po.Result;
import com.hcsy.spring.po.User;
import com.hcsy.spring.service.UserService;

import cn.hutool.core.bean.BeanUtil;
import feign.Param;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;

import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/users")
@RequiredArgsConstructor
@Tag(name = "用户模块", description = "用户相关接口")
public class UserController {
    private final UserService userService;

    @GetMapping
    @Operation(summary = "获取用户信息", description = "获取用户信息列表")
    public Result listUsers() {
        return Result.success(userService.list());
    }

    @PostMapping
    @Operation(summary = "新增用户", description = "通过请求体创建用户信息")
    public Result addUser(@RequestBody UserCreateDTO userDto) {
        User user = BeanUtil.copyProperties(userDto, User.class);
        userService.save(user);
        return Result.success();
    }

    @DeleteMapping("/{id}")
    @Operation(summary = "删除用户", description = "根据id删除用户")
    public Result deleteUser(@Param Long id) {
        userService.removeById(id);
        return Result.success();
    }

    @GetMapping("/{id}")
    @Operation(summary = "查询用户", description = "根据id查询用户")
    public Result getUserById(@Param Long id) {
        User user = userService.getById(id);
        return Result.success(user);
    }

    @PutMapping
    @Operation(summary = "修改用户", description = "通过请求体修改用户信息")
    public Result updateUser(@RequestBody UserUpdateDTO userDto) {
        User user = BeanUtil.copyProperties(userDto, User.class);
        userService.updateById(user);
        return Result.success();
    }
}

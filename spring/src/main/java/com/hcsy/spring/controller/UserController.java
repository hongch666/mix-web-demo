package com.hcsy.spring.controller;

import com.hcsy.spring.po.User;
import com.hcsy.spring.service.UserService;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/users")
@Tag(name = "用户模块", description = "用户相关接口")
public class UserController {

    @Autowired
    private UserService userService;

    @GetMapping
    @Operation(summary = "获取用户信息", description = "获取用户信息列表")
    public List<User> listUsers() {
        return userService.list();
    }

    @PostMapping
    @Operation(summary = "新增用户", description = "通过请求体创建用户信息")
    public boolean addUser(@RequestBody User user) {
        return userService.save(user);
    }
}

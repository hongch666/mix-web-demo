package com.hcsy.spring.controller;

import com.hcsy.spring.po.User;
import com.hcsy.spring.service.UserService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/users")
public class UserController {
    @Autowired
    private UserService userService;

    @GetMapping
    public List<User> listUsers() {
        return userService.list();
    }

    @PostMapping
    public boolean addUser(@RequestBody User user) {
        return userService.save(user);
    }
}

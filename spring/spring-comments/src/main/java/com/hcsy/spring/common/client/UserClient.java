package com.hcsy.spring.common.client;

import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;

import com.hcsy.spring.entity.po.Result;

@FeignClient(name = "spring-user")
public interface UserClient {
    @GetMapping("/users/{id}")
    public Result getById(@PathVariable Long id);

    @GetMapping("/users/find/{username}")
    public Result findByUsername(@PathVariable String username);

    @GetMapping("/users/find/all/{username}")
    public Result listAllUserByUsername(@PathVariable String username);
}

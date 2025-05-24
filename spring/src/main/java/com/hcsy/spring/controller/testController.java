package com.hcsy.spring.controller;

import com.hcsy.spring.client.GinClient;
import com.hcsy.spring.client.NestjsClient;
import com.hcsy.spring.po.Result;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api_spring")
@RequiredArgsConstructor
public class testController {
    private final GinClient ginClient;
    private final NestjsClient nestjsClient;

    @GetMapping("/spring")
    public Result getHello()
    {
        return Result.success("Hello,I am Spring!");
    }

    @GetMapping("/gin")
    public Result gerGin()
    {
        return ginClient.testGin();
    }

    @GetMapping("/nestjs")
    public Result gerNestjs()
    {
        return nestjsClient.testNestjs();
    }
}

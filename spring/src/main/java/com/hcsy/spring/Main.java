package com.hcsy.spring;

import org.springframework.boot.SpringApplication;
import com.hcsy.spring.core.annotation.Starter;

@Starter
public class Main {

    public static void main(String[] args) {
        // 启动 Spring Boot 应用
        SpringApplication.run(Main.class, args);
    }

}

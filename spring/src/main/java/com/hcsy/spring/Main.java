package com.hcsy.spring;

import org.springframework.boot.SpringApplication;

import com.hcsy.spring.bootstrap.DotenvInitializer;
import com.hcsy.spring.bootstrap.Starter;

/**
 * 应用启动入口，先加载 .env 环境变量再启动 Spring Boot 应用
 */
@Starter
public class Main {
    /**
     * 加载 .env 环境变量后启动 Spring Boot 应用
     */
    public static void main(String[] args) {
        // 在应用启动前加载.env文件中的环境变量
        DotenvInitializer.loadEnv();
        // 启动 Spring Boot 应用
        SpringApplication.run(Main.class, args);
    }
}

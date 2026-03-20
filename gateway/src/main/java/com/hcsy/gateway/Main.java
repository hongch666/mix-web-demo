package com.hcsy.gateway;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

import com.hcsy.gateway.config.DotenvInitializer;

@SpringBootApplication
public class Main {

    public static void main(String[] args) {
        // 在应用启动前加载.env文件中的环境变量
        DotenvInitializer.loadEnv();
        // 启动 Spring Boot 应用
        SpringApplication.run(Main.class, args);
    }

}

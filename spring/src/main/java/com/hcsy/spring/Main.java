package com.hcsy.spring;

import org.springframework.boot.SpringApplication;
import com.hcsy.spring.core.annotation.Starter;
import com.hcsy.spring.infra.initializer.DotenvInitializer;

@Starter
public class Main {

    public static void main(String[] args) {
        // 在应用启动前加载.env文件中的环境变量
        DotenvInitializer.loadEnv();
        // 启动 Spring Boot 应用
        SpringApplication.run(Main.class, args);
    }

}

package com.hcsy.spring;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.openfeign.EnableFeignClients;

// TODO: 文章查询使用ES的搜索功能
// TODO: 文章增删改后调用Gin部分的同步代码（要有事务注解）
// TODO: 文章增删改查后使用NestJS部分的创建日志功能增加日志
// TODO: 增加对Redis的调用
// TODO: 使用Redis存储用户状态（在线/离线）
// TODO: 增加分页查询的处理和对应的类

@EnableFeignClients()
@SpringBootApplication
@MapperScan(basePackages = "com.hcsy.spring.mapper")
public class Application {

    public static void main(String[] args) {
        SpringApplication.run(Application.class, args);
    }

}

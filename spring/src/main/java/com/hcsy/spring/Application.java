package com.hcsy.spring;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.openfeign.EnableFeignClients;

// TODO: 增加文章模块的增删改，查询使用ES的搜索功能
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

package com.hcsy.spring;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.openfeign.EnableFeignClients;
import org.springframework.context.annotation.EnableAspectJAutoProxy;

// TODO: 文章增删改后调用Gin部分的同步代码（要有事务注解）
// TODO: 文章增删改查后使用NestJS部分的创建日志功能增加日志
// TODO: 日志创建部分不使用feign客户端调用，而是将日志内容生产到RabbitMQ中
// TODO: 增加发布文章功能（修改发布状态），注意要同时同步到ES中,并且发送消息到RabbitMQ中
// TODO: 使用定时任务，每天0点检查是否有文章未发布，自动发布（调用上述逻辑）

@EnableFeignClients()
@SpringBootApplication
@EnableAspectJAutoProxy(proxyTargetClass = true)
@MapperScan(basePackages = "com.hcsy.spring.mapper")
public class Application {

    public static void main(String[] args) {
        SpringApplication.run(Application.class, args);
    }

}

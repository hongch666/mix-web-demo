package com.hcsy.spring;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.openfeign.EnableFeignClients;
import org.springframework.context.annotation.EnableAspectJAutoProxy;
import org.springframework.scheduling.annotation.EnableScheduling;

// TODO: 网关修改对应路由规则，开放部分接口，并且手动使用postman写出对应的接口
// TODO: 增加查询用户状态功能
// TODO: 实现登录登出逻辑，并且修改对应登录状态
// TODO: ThreadLocal存储用户id，并且服务间调用在请求体中传递用户id，实现后增删改文章时判断一下用户是否正确
// TODO: 网关使用拦截器进行JWT登录校验

@EnableFeignClients()
@SpringBootApplication
@EnableScheduling
@EnableAspectJAutoProxy(proxyTargetClass = true)
@MapperScan(basePackages = "com.hcsy.spring.mapper")
public class Application {

    public static void main(String[] args) {
        SpringApplication.run(Application.class, args);
    }

}

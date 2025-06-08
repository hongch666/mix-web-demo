package com.hcsy.spring;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.openfeign.EnableFeignClients;
import org.springframework.context.annotation.EnableAspectJAutoProxy;

// TODO: 增加根据用户id查询文章
// TODO: 使用事务让AOP的内容同时执行
// TODO: 增加发布文章功能（修改发布状态），注意要同时同步到ES中,并且发送消息到RabbitMQ中
// TODO: 使用定时任务，每天0点检查是否有文章未发布，自动发布（调用上述逻辑）
// TODO: 实现登录登出逻辑，并且修改对应登录状态
// TODO: ThreadLocal存储用户id，并且服务间调用在请求体中传递用户id，实现后增删改文章时判断一下用户是否正确
// TODO: 网关修改对应路由规则，开放部分接口
// TODO: 网关使用拦截器进行JWT登录校验

@EnableFeignClients()
@SpringBootApplication
@EnableAspectJAutoProxy(proxyTargetClass = true)
@MapperScan(basePackages = "com.hcsy.spring.mapper")
public class Application {

    public static void main(String[] args) {
        SpringApplication.run(Application.class, args);
    }

}

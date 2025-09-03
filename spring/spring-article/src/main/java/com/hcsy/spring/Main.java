package com.hcsy.spring;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.ApplicationRunner;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cache.annotation.EnableCaching;
import org.springframework.cloud.openfeign.EnableFeignClients;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.EnableAspectJAutoProxy;
import org.springframework.core.env.Environment;
import org.springframework.scheduling.annotation.EnableScheduling;
import lombok.extern.slf4j.Slf4j;

@EnableFeignClients()
@SpringBootApplication
@EnableScheduling
@EnableAspectJAutoProxy(proxyTargetClass = true)
@EnableCaching
@MapperScan(basePackages = "com.hcsy.spring.api.mapper")
@Slf4j
public class Main {

    public static void main(String[] args) {
        SpringApplication.run(Main.class, args);
    }

    @Bean
    ApplicationRunner applicationRunner(Environment env) {
        return args -> {
            String ip = "localhost";
            String port = env.getProperty("server.port", "8081");
            log.info("Spring Boot应用已启动");
            log.info("服务地址: http://{}:{}/", ip, port);
            log.info("Swagger文档地址: http://{}:{}/swagger-ui/index.html", ip, port);
        };
    }

}

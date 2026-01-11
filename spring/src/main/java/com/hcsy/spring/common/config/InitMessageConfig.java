package com.hcsy.spring.common.config;

import org.springframework.boot.ApplicationRunner;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.core.env.Environment;

import lombok.extern.slf4j.Slf4j;

@Configuration
@Slf4j
public class InitMessageConfig {
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

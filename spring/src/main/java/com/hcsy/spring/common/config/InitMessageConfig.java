package com.hcsy.spring.common.config;

import org.springframework.boot.ApplicationRunner;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.core.env.Environment;

import com.hcsy.spring.common.utils.Constants;

import lombok.extern.slf4j.Slf4j;

@Configuration
@Slf4j
public class InitMessageConfig {
    @Bean
    ApplicationRunner applicationRunner(Environment env) {
        return args -> {
            String ip = Constants.INIT_IP;
            String port = env.getProperty("server.port", Constants.INIT_PORT);
            log.info(Constants.INIT_MSG);
            log.info(Constants.INIT_ADDR, ip, port);
            log.info(Constants.INIT_SWAGGER_ADDR, ip, port);
        };
    }
}

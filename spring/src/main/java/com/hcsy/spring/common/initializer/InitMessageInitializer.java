package com.hcsy.spring.common.initializer;

import org.springframework.boot.ApplicationArguments;
import org.springframework.boot.ApplicationRunner;
import org.springframework.core.env.Environment;
import org.springframework.stereotype.Component;

import com.hcsy.spring.common.utils.Constants;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

@Component
@RequiredArgsConstructor
@Slf4j
public class InitMessageInitializer implements ApplicationRunner {

    private final Environment env;

    @Override
    public void run(ApplicationArguments args) {
        String ip = Constants.INIT_IP;
        String port = env.getProperty("server.port", Constants.INIT_PORT);
        log.info(Constants.INIT_MSG);
        log.info(Constants.INIT_ADDR, ip, port);
        log.info(Constants.INIT_SWAGGER_ADDR, ip, port);
    }
}
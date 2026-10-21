package com.hcsy.spring.bootstrap;

import org.springframework.boot.ApplicationArguments;
import org.springframework.boot.ApplicationRunner;
import org.springframework.core.env.Environment;
import org.springframework.stereotype.Component;

import com.hcsy.spring.common.constants.Defaults;
import com.hcsy.spring.common.utils.SimpleLogger;

import lombok.RequiredArgsConstructor;

/**
 * 启动完成提示初始化器，在应用启动完成后输出服务地址与 Swagger 文档地址
 */
@Component
@RequiredArgsConstructor
public class InitMessageInitializer implements ApplicationRunner {

    private final SimpleLogger logger;
    private final Environment env;

    /**
     * 应用启动完成后输出服务地址与 Swagger 文档地址
     */
    @Override
    public void run(ApplicationArguments args) {
        String ip = Defaults.INIT_IP;
        String port = env.getProperty("server.port", Defaults.INIT_PORT);
        logger.info(Defaults.INIT_MSG);
        logger.info(Defaults.INIT_ADDR, ip, port);
        logger.info(Defaults.INIT_SWAGGER_ADDR, ip, port);
    }
}

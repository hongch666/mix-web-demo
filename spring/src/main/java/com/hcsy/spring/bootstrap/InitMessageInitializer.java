package com.hcsy.spring.bootstrap;

import org.springframework.boot.ApplicationArguments;
import org.springframework.boot.ApplicationRunner;
import org.springframework.stereotype.Component;

import com.hcsy.spring.common.constants.Defaults;
import com.hcsy.spring.common.utils.SimpleLogger;
import com.hcsy.spring.config.properties.ServerProperties;

import lombok.RequiredArgsConstructor;

/**
 * 启动完成提示初始化器，在应用启动完成后输出运行模式、服务地址与 Swagger 文档地址
 */
@Component
@RequiredArgsConstructor
public class InitMessageInitializer implements ApplicationRunner {

    private final SimpleLogger logger;
    private final ServerProperties serverProperties;

    /**
     * 应用启动完成后输出运行模式、服务地址与 Swagger 文档地址
     */
    @Override
    public void run(ApplicationArguments args) {
        String mode = serverProperties.mode();
        String address = serverProperties.address();
        int port = serverProperties.port();
        logger.info(Defaults.INIT_MSG);
        logger.info(Defaults.INIT_MODE, mode);
        logger.info(Defaults.INIT_ADDR, address, port);
        logger.info(Defaults.INIT_SWAGGER_ADDR, address, port);
    }
}

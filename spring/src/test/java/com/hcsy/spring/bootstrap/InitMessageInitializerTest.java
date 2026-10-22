package com.hcsy.spring.bootstrap;

import static org.mockito.Mockito.*;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import com.hcsy.spring.common.constants.Defaults;
import com.hcsy.spring.common.utils.SimpleLogger;
import com.hcsy.spring.config.properties.ServerProperties;

class InitMessageInitializerTest {
    // 验证该场景的预期行为
    @Test
    @DisplayName("启动时输出运行模式与服务地址")
    void logsStartupAddress() {
        SimpleLogger logger = mock(SimpleLogger.class);
        new InitMessageInitializer(logger, new ServerProperties("dev", 9000)).run(null);
        verify(logger).info(Defaults.INIT_MSG);
        verify(logger).info(Defaults.INIT_MODE, "dev");
        verify(logger).info(Defaults.INIT_ADDR, Defaults.INIT_IP, 9000);
        verify(logger).info(Defaults.INIT_SWAGGER_ADDR, Defaults.INIT_IP, 9000);
    }
}

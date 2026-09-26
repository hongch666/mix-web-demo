package com.hcsy.spring.infra.initializer;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.core.env.Environment;

import com.hcsy.spring.common.constants.Defaults;
import com.hcsy.spring.common.utils.SimpleLogger;

import static org.mockito.Mockito.*;

class InitMessageInitializerTest {
    // 验证该场景的预期行为
    @Test
    @DisplayName("启动时输出服务地址")
    void logsStartupAddress() {
        SimpleLogger logger = mock(SimpleLogger.class);
        Environment env = mock(Environment.class);
        when(env.getProperty("server.port", "8081")).thenReturn("9000");
        new InitMessageInitializer(logger, env).run(null);
        verify(logger).info(Defaults.INIT_MSG);
        verify(logger, times(2)).info(anyString(), anyString(), anyString());
    }
}

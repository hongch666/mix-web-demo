package com.hcsy.spring.infra.handler;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.mockito.Mockito.mock;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import com.hcsy.spring.common.constants.HttpCode;
import com.hcsy.spring.common.exceptions.BusinessException;
import com.hcsy.spring.common.utils.SimpleLogger;

import reactor.test.StepVerifier;

class GlobalExceptionHandlerTest {
    // 验证该场景的预期行为
    @Test
    @DisplayName("业务异常映射为对应 HTTP 状态")
    void mapsBusinessException() {
        var handler = new GlobalExceptionHandler(mock(SimpleLogger.class));
        var ex = BusinessException.builder().httpStatus(HttpCode.CONFLICT).errorMessage("conflict").build();
        StepVerifier.create(handler.handleBusinessException(ex)).assertNext(response -> assertEquals(HttpCode.CONFLICT,
            response.getStatusCode().value())).verifyComplete();
    }

    // 验证该场景的预期行为

    @Test
    @DisplayName("未知异常映射为 500")
    void mapsUnknownException() {
        var handler = new GlobalExceptionHandler(mock(SimpleLogger.class));
        StepVerifier.create(handler.handleException(new IllegalStateException()))
            .assertNext(response -> assertEquals(500, response.getStatusCode().value())).verifyComplete();
    }
}

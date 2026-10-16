package com.hcsy.spring.web.exception;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.mockito.Mockito.mock;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.core.MethodParameter;
import org.springframework.validation.BeanPropertyBindingResult;
import org.springframework.validation.FieldError;
import org.springframework.web.bind.support.WebExchangeBindException;
import org.springframework.web.server.ServerWebInputException;

import com.hcsy.spring.common.constants.HttpCode;
import com.hcsy.spring.common.constants.Messages;
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

    @Test
    @DisplayName("字段校验失败返回 400 和字段提示")
    void mapsFieldValidationException() {
        var handler = new GlobalExceptionHandler(mock(SimpleLogger.class));
        var bindingResult = new BeanPropertyBindingResult(new Object(), "request");
        bindingResult.addError(new FieldError("request", "name", "名称不能为空"));
        var ex = new WebExchangeBindException(mock(MethodParameter.class), bindingResult);

        StepVerifier.create(handler.handleValidationException(ex)).assertNext(response -> {
            assertEquals(HttpCode.BAD_REQUEST, response.getStatusCode().value());
            assertNotNull(response.getBody());
            assertEquals(HttpCode.BAD_REQUEST, response.getBody().getCode());
            assertEquals("名称不能为空", response.getBody().getMsg());
        }).verifyComplete();
    }

    @Test
    @DisplayName("请求体格式错误返回 400 且不暴露框架异常")
    void mapsMalformedRequestException() {
        var handler = new GlobalExceptionHandler(mock(SimpleLogger.class));

        StepVerifier.create(handler.handleValidationException(new ServerWebInputException("invalid JSON")))
            .assertNext(response -> {
                assertEquals(HttpCode.BAD_REQUEST, response.getStatusCode().value());
                assertNotNull(response.getBody());
                assertEquals(HttpCode.BAD_REQUEST, response.getBody().getCode());
                assertEquals(Messages.REQUEST_BODY_INVALID, response.getBody().getMsg());
            }).verifyComplete();
    }
}

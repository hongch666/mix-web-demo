package com.hcsy.spring.infra.handler;

import org.springframework.http.ResponseEntity;
import org.springframework.validation.BindException;
import org.springframework.validation.BindingResult;
import org.springframework.validation.FieldError;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.bind.support.WebExchangeBindException;
import org.springframework.web.server.ServerWebInputException;

import com.hcsy.spring.common.constants.HttpCode;
import com.hcsy.spring.common.constants.Messages;
import com.hcsy.spring.common.exceptions.BusinessException;
import com.hcsy.spring.common.utils.Result;
import com.hcsy.spring.common.utils.SimpleLogger;

import jakarta.validation.ConstraintViolation;
import jakarta.validation.ConstraintViolationException;
import lombok.RequiredArgsConstructor;
import reactor.core.publisher.Mono;

@RestControllerAdvice
@RequiredArgsConstructor
public class GlobalExceptionHandler {
    private final SimpleLogger logger;

    /**
     * 处理业务异常
     */
    @ExceptionHandler(BusinessException.class)
    public Mono<ResponseEntity<Result<?>>> handleBusinessException(BusinessException ex) {
        logger.error(Messages.BUSINESS_EXCEPTION + ex.getMessage(), ex);
        return Mono.just(ResponseEntity
            .status(ex.getHttpStatus())
            .body(Result.error(ex.getHttpStatus(), ex.getErrorMessage())));
    }

    /**
     * 处理参数校验异常
     *
     * WebFlux 下 @Valid 失败抛的是 WebExchangeBindException，请求体格式错误或参数类型不匹配抛
     * ServerWebInputException，二者都不是 MVC 的 MethodArgumentNotValidException/BindException，
     * 必须在此显式声明，否则会被兜底分支吞成 500 并丢失字段级消息
     */
    @ExceptionHandler({ WebExchangeBindException.class, ServerWebInputException.class,
        MethodArgumentNotValidException.class, BindException.class,
        ConstraintViolationException.class })
    public Mono<ResponseEntity<Result<?>>> handleValidationException(Exception ex) {
        String message = extractValidationMessage(ex);
        logger.error(Messages.SYSTEM_EXCEPTION + message, ex);
        return Mono.just(ResponseEntity
            .status(HttpCode.BAD_REQUEST)
            .body(Result.error(HttpCode.BAD_REQUEST, message)));
    }

    /**
     * 处理其他异常
     */
    @ExceptionHandler(Exception.class)
    public Mono<ResponseEntity<Result<?>>> handleException(Exception ex) {
        logger.error(Messages.SYSTEM_EXCEPTION + ex.getMessage(), ex);
        return Mono.just(ResponseEntity
            .status(HttpCode.INTERNAL_SERVER_ERROR)
            .body(Result.error(HttpCode.INTERNAL_SERVER_ERROR, Messages.SYSTEM_EXCEPTION_BACK)));
    }

    private String extractValidationMessage(Exception ex) {
        if (ex instanceof WebExchangeBindException webExchangeBindException) {
            return extractFieldMessage(webExchangeBindException.getBindingResult());
        }

        if (ex instanceof MethodArgumentNotValidException methodArgumentNotValidException) {
            return extractFieldMessage(methodArgumentNotValidException.getBindingResult());
        }

        if (ex instanceof BindException bindException) {
            return extractFieldMessage(bindException.getBindingResult());
        }

        if (ex instanceof ConstraintViolationException constraintViolationException) {
            return constraintViolationException.getConstraintViolations().stream()
                .map(ConstraintViolation::getMessage)
                .filter(message -> message != null && !message.isBlank())
                .findFirst()
                .orElse(Messages.SYSTEM_EXCEPTION_BACK);
        }

        // 请求体格式错误、参数类型不匹配等，不向前端暴露框架细节
        if (ex instanceof ServerWebInputException) {
            return Messages.REQUEST_BODY_INVALID;
        }

        return Messages.SYSTEM_EXCEPTION_BACK;
    }

    private String extractFieldMessage(BindingResult bindingResult) {
        if (bindingResult == null) {
            return Messages.SYSTEM_EXCEPTION_BACK;
        }

        FieldError fieldError = bindingResult.getFieldError();
        String message = fieldError == null ? null : fieldError.getDefaultMessage();
        if (message != null && !message.isBlank()) {
            return message;
        }

        return Messages.SYSTEM_EXCEPTION_BACK;
    }
}

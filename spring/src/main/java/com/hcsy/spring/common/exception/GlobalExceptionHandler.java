package com.hcsy.spring.common.exception;

import com.hcsy.spring.common.utils.Result;
import com.hcsy.spring.common.utils.SimpleLogger;

import lombok.RequiredArgsConstructor;

import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

@RestControllerAdvice
@RequiredArgsConstructor
public class GlobalExceptionHandler {
    private final SimpleLogger logger;

    @ExceptionHandler(Exception.class)
    public Result ex(Exception ex) {
        logger.error("捕获到异常: " + ex.getMessage());
        return Result.error(ex.getMessage());
    }
}

package com.hcsy.spring.exception;

import com.hcsy.spring.po.Result;
import com.hcsy.spring.utils.SimpleLogger;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

@RestControllerAdvice
@Slf4j
@RequiredArgsConstructor
public class GlobalExceptionHandler {
    private final SimpleLogger logger;

    @ExceptionHandler(Exception.class)
    public Result ex(Exception ex) {
        logger.error("捕获到异常: " + ex.getMessage());
        return Result.error(ex.getMessage());
    }
}

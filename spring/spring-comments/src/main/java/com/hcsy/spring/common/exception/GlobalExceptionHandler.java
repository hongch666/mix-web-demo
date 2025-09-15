package com.hcsy.spring.common.exception;

import com.hcsy.spring.common.utils.SimpleLogger;
import com.hcsy.spring.entity.po.Result;

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
